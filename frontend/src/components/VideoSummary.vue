<template>
  <section class="summary-panel">
    <div class="summary-card">
      <div class="summary-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          class="summary-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <span>{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <div class="summary-body">
        <div v-if="loading && !summaryText && activeTab === 'summary'" class="summary-center">
          <div class="summary-spinner lg"></div>
          <p class="summary-muted">{{ loadingMessage }}</p>
        </div>

        <div v-show="activeTab === 'summary'">
          <div v-if="summaryText" class="summary-prose" v-html="renderedSummary"></div>
          <div v-if="loading && summaryText" class="summary-stream-hint">
            <span class="pulse-dot"></span>
            AI 正在生成中...
          </div>
        </div>

        <div v-show="activeTab === 'subtitle'">
          <div v-if="subtitleData.segments && subtitleData.segments.length > 0">
            <div class="subtitle-head">
              <div class="summary-muted">
                共 {{ subtitleData.segments.length }} 条字幕
                <span v-if="subtitleData.language" class="subtitle-badge">
                  {{ subtitleData.subtitle_type === "manual" ? "人工字幕" : "自动字幕" }} · {{ subtitleData.language }}
                </span>
              </div>
              <button type="button" class="subtitle-toggle" @click="subtitleExpanded = !subtitleExpanded">
                {{ subtitleExpanded ? "收起" : "展开全部" }}
              </button>
            </div>
            <div class="subtitle-list" :class="{ expanded: subtitleExpanded }">
              <div v-for="(seg, idx) in subtitleData.segments" :key="idx" class="subtitle-row">
                <span class="subtitle-time">{{ formatTime(seg.start) }}</span>
                <span class="subtitle-text">{{ seg.text }}</span>
              </div>
            </div>
          </div>
          <div v-else-if="!loading" class="summary-center">
            <p class="summary-muted">该视频暂无可用字幕</p>
          </div>
          <div v-else class="summary-center">
            <div class="summary-spinner"></div>
            <p class="summary-muted">正在提取字幕...</p>
          </div>
        </div>

        <div v-show="activeTab === 'mindmap'">
          <div v-if="mindmapMarkdown" class="mindmap-wrap">
            <svg ref="mindmapSvg" class="mindmap-svg"></svg>
          </div>
          <div v-else-if="loading" class="summary-center">
            <div class="summary-spinner"></div>
            <p class="summary-muted">正在生成思维导图...</p>
          </div>
          <div v-else class="summary-center">
            <p class="summary-muted">请先生成总结以查看思维导图</p>
          </div>
        </div>

        <div v-show="activeTab === 'qa'">
          <div class="qa-wrap">
            <div ref="chatContainer" class="qa-messages">
              <div v-if="chatMessages.length === 0" class="summary-center compact">
                <p class="summary-muted">向 AI 提问关于这个视频的任何问题</p>
                <p class="summary-muted small">例如：「这个视频的核心观点是什么？」</p>
              </div>
              <div
                v-for="(msg, idx) in chatMessages"
                :key="idx"
                class="qa-row"
                :class="msg.role === 'user' ? 'user' : 'assistant'"
              >
                <div class="qa-bubble" :class="msg.role">
                  <div v-if="msg.role === 'assistant'" v-html="renderMarkdown(msg.content)"></div>
                  <span v-else>{{ msg.content }}</span>
                  <span v-if="msg.role === 'assistant' && msg.loading" class="typing-cursor"></span>
                </div>
              </div>
            </div>
            <div class="qa-input-row">
              <input
                v-model="chatInput"
                type="text"
                placeholder="输入你的问题..."
                class="qa-input"
                :disabled="chatLoading"
                @keydown.enter.prevent="sendQuestion"
              />
              <button type="button" class="qa-send" :disabled="!chatInput.trim() || chatLoading" @click="sendQuestion">
                {{ chatLoading ? "发送中..." : "发送" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from "vue";
import { marked } from "marked";
import { Transformer } from "markmap-lib";
import { Markmap } from "markmap-view";
import { summarizeVideo, chatWithVideo } from "../api/summarize.js";

const props = defineProps({
  videoUrl: { type: String, required: true },
  videoTitle: { type: String, default: "" },
});

const emit = defineEmits(["error"]);

const tabs = [
  { key: "summary", label: "总结摘要", icon: "📝" },
  { key: "subtitle", label: "字幕文本", icon: "📄" },
  { key: "mindmap", label: "思维导图", icon: "🧠" },
  { key: "qa", label: "AI 问答", icon: "💬" },
];

const activeTab = ref("summary");
const loading = ref(false);
const loadingMessage = ref("正在提取视频字幕...");

const summaryText = ref("");
const subtitleData = ref({ segments: [], has_subtitle: false });
const subtitleExpanded = ref(false);
const mindmapMarkdown = ref("");
const mindmapSvg = ref(null);

const chatMessages = ref([]);
const chatInput = ref("");
const chatLoading = ref(false);
const chatContainer = ref(null);

const renderedSummary = ref("");

watch(summaryText, (val) => {
  renderedSummary.value = renderMarkdown(val);
});

watch(mindmapMarkdown, async (val) => {
  if (val) {
    await nextTick();
    renderMindmap(val);
  }
});

function renderMarkdown(text) {
  if (!text) return "";
  return marked.parse(text);
}

function renderMindmap(md) {
  if (!mindmapSvg.value) return;
  try {
    mindmapSvg.value.innerHTML = "";
    const transformer = new Transformer();
    const { root } = transformer.transform(md);
    Markmap.create(mindmapSvg.value, { autoFit: true }, root);
  } catch (e) {
    console.warn("思维导图渲染失败:", e);
  }
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

async function startSummarize() {
  loading.value = true;
  summaryText.value = "";
  mindmapMarkdown.value = "";
  loadingMessage.value = "正在提取视频字幕...";

  try {
    await summarizeVideo(props.videoUrl, "zh", {
      subtitle: (data) => {
        try {
          subtitleData.value = JSON.parse(data);
          if (subtitleData.value.has_subtitle) {
            loadingMessage.value = "AI 正在分析视频内容...";
          }
        } catch {
          /* ignore */
        }
      },
      summary: (data) => {
        summaryText.value += data;
      },
      mindmap: (data) => {
        try {
          const parsed = JSON.parse(data);
          mindmapMarkdown.value = parsed.markdown || "";
        } catch {
          /* ignore */
        }
      },
      done: () => {
        loading.value = false;
      },
      error: (data) => {
        loading.value = false;
        try {
          const parsed = JSON.parse(data);
          emit("error", parsed.message || "总结失败");
        } catch {
          emit("error", `总结失败: ${data}`);
        }
      },
    });
  } catch (err) {
    loading.value = false;
    emit("error", `总结请求失败: ${err.message}`);
  }
}

async function sendQuestion() {
  const question = chatInput.value.trim();
  if (!question || chatLoading.value) return;

  chatInput.value = "";
  chatMessages.value.push({ role: "user", content: question });

  const aiMessage = { role: "assistant", content: "", loading: true };
  chatMessages.value.push(aiMessage);
  chatLoading.value = true;

  await nextTick();
  scrollChatToBottom();

  try {
    await chatWithVideo(props.videoUrl, question, subtitleData.value.full_text || "", {
      answer: (data) => {
        aiMessage.content += data;
        scrollChatToBottom();
      },
      done: () => {
        aiMessage.loading = false;
        chatLoading.value = false;
      },
      error: (data) => {
        aiMessage.loading = false;
        chatLoading.value = false;
        try {
          const parsed = JSON.parse(data);
          aiMessage.content = `❌ ${parsed.message || "回答失败"}`;
        } catch {
          aiMessage.content = "❌ 回答失败";
        }
      },
    });
  } catch (err) {
    aiMessage.loading = false;
    chatLoading.value = false;
    aiMessage.content = `❌ 请求失败: ${err.message}`;
  }
}

function scrollChatToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  });
}

onMounted(() => {
  startSummarize();
});
</script>

<style scoped>
.summary-panel {
  margin-top: 4px;
}

.summary-card {
  background: #fff;
  border-radius: 18px;
  border: 1px solid var(--line-light);
  overflow: hidden;
  box-shadow: 0 6px 20px rgba(17, 24, 39, 0.04);
}

.summary-tabs {
  display: flex;
  border-bottom: 1px solid var(--line-light);
  overflow-x: auto;
}

.summary-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px;
  border: none;
  background: transparent;
  color: var(--muted);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  position: relative;
  white-space: nowrap;
}

.summary-tab.active {
  color: var(--blue);
}

.summary-tab.active::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: var(--blue);
}

.summary-body {
  padding: 18px 20px 20px;
  min-height: 320px;
}

.summary-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  gap: 12px;
}

.summary-center.compact {
  padding: 28px 16px;
}

.summary-muted {
  color: var(--muted);
  font-size: 14px;
}

.summary-muted.small {
  font-size: 12px;
}

.summary-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(47, 111, 237, 0.18);
  border-top-color: var(--blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.summary-spinner.lg {
  width: 44px;
  height: 44px;
}

.summary-stream-hint {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--soft);
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--blue);
  animation: pulse 1s ease-in-out infinite;
}

.subtitle-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.subtitle-badge {
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--blue-soft);
  color: var(--blue);
  font-size: 12px;
}

.subtitle-toggle {
  border: none;
  background: transparent;
  color: var(--blue);
  font-size: 12px;
  cursor: pointer;
}

.subtitle-list {
  max-height: 420px;
  overflow-y: auto;
  display: grid;
  gap: 4px;
}

.subtitle-list.expanded {
  max-height: none;
}

.subtitle-row {
  display: flex;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 10px;
}

.subtitle-row:hover {
  background: #f8fafc;
}

.subtitle-time {
  flex-shrink: 0;
  min-width: 56px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: var(--blue);
  padding-top: 2px;
}

.subtitle-text {
  font-size: 14px;
  line-height: 1.6;
}

.mindmap-wrap {
  border: 1px solid var(--line-light);
  border-radius: 14px;
  background: #f8fafc;
  overflow: hidden;
}

.mindmap-svg {
  width: 100%;
  min-height: 460px;
  display: block;
}

.qa-wrap {
  display: grid;
  gap: 12px;
}

.qa-messages {
  max-height: 360px;
  overflow-y: auto;
  display: grid;
  gap: 12px;
  padding-right: 4px;
}

.qa-row {
  display: flex;
}

.qa-row.user {
  justify-content: flex-end;
}

.qa-row.assistant {
  justify-content: flex-start;
}

.qa-bubble {
  max-width: 82%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.65;
}

.qa-bubble.user {
  background: var(--blue);
  color: #fff;
  border-bottom-right-radius: 6px;
}

.qa-bubble.assistant {
  background: #f8fafc;
  color: var(--ink);
  border: 1px solid var(--line-light);
  border-bottom-left-radius: 6px;
}

.qa-input-row {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid var(--line-light);
}

.qa-input {
  flex: 1;
  height: 44px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
}

.qa-input:focus {
  outline: none;
  border-color: var(--blue);
  box-shadow: 0 0 0 3px rgba(47, 111, 237, 0.12);
}

.qa-send {
  height: 44px;
  padding: 0 18px;
  border: none;
  border-radius: 12px;
  background: var(--blue);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.qa-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.typing-cursor {
  display: inline-block;
  width: 6px;
  height: 14px;
  margin-left: 2px;
  background: rgba(47, 111, 237, 0.55);
  border-radius: 2px;
  vertical-align: text-bottom;
  animation: pulse 0.8s ease-in-out infinite;
}

.summary-prose :deep(h2) {
  font-size: 1.125rem;
  font-weight: 700;
  margin: 1.25rem 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--line-light);
}

.summary-prose :deep(h3) {
  font-size: 1rem;
  font-weight: 600;
  margin: 1rem 0 0.5rem;
}

.summary-prose :deep(p),
.summary-prose :deep(li) {
  line-height: 1.75;
  margin-bottom: 0.5rem;
}

.summary-prose :deep(ul),
.summary-prose :deep(ol) {
  padding-left: 1.4rem;
  margin-bottom: 0.75rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.45;
  }
  50% {
    opacity: 1;
  }
}
</style>
