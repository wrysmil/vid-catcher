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

        <div v-show="activeTab === 'summary'" ref="summaryContainer" class="summary-output-wrap">
          <div v-if="summaryStreaming" class="summary-stream-text">
            {{ summaryText }}<span class="typing-cursor"></span>
          </div>
          <div v-else-if="summaryText" class="summary-prose" v-html="renderedSummary"></div>
          <div v-if="summaryStreaming" class="summary-stream-hint">
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
                  {{ subtitleTypeLabel(subtitleData.subtitle_type) }} · {{ subtitleData.language }}
                </span>
              </div>
              <div class="subtitle-head-actions">
                <div
                  v-if="subtitleData.segments.length"
                  ref="subtitleDropdownRef"
                  class="export-menu"
                >
                  <button
                    type="button"
                    class="export-btn"
                    :aria-expanded="showSubtitleDropdown"
                    aria-haspopup="true"
                    @click.stop="showSubtitleDropdown = !showSubtitleDropdown"
                  >
                    下载字幕
                  </button>
                  <div v-if="showSubtitleDropdown" class="export-pop" role="menu">
                    <button
                      v-for="fmt in subtitleFormats"
                      :key="fmt.key"
                      type="button"
                      class="export-item"
                      role="menuitem"
                      @click="downloadSubtitle(fmt.key)"
                    >
                      {{ fmt.label }}
                      <span class="export-ext">.{{ fmt.ext }}</span>
                    </button>
                  </div>
                </div>
                <button type="button" class="subtitle-toggle" @click="subtitleExpanded = !subtitleExpanded">
                  {{ subtitleExpanded ? "收起" : "展开全部" }}
                </button>
              </div>
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
          <div v-if="mindmapMarkdown" ref="mindmapContainer" class="mindmap-wrap" :class="{ fullscreen: isFullscreen }">
            <div class="mindmap-toolbar">
              <button type="button" class="export-btn" @click="onDownloadPng">PNG</button>
              <button type="button" class="export-btn" @click="onDownloadSvg">SVG</button>
              <button type="button" class="export-btn" @click="toggleFullscreen">
                {{ isFullscreen ? "退出全屏" : "全屏" }}
              </button>
            </div>
            <p v-if="exportHint" class="summary-muted small">{{ exportHint }}</p>
            <svg ref="mindmapSvg" class="mindmap-svg"></svg>
          </div>
          <div v-else-if="mindmapLoading" class="summary-center">
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
                  <div v-if="msg.role === 'assistant' && msg.loading" class="qa-stream-text">
                    <template v-if="msg.content">{{ msg.content }}</template>
                    <span v-else class="summary-muted">AI 正在回复</span>
                    <span class="typing-cursor"></span>
                  </div>
                  <div v-else-if="msg.role === 'assistant'" class="chat-prose" v-html="renderMarkdown(msg.content)"></div>
                  <span v-else>{{ msg.content }}</span>
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
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from "vue";
import { marked } from "marked";
import { Transformer } from "markmap-lib";
import { Markmap } from "markmap-view";
import { summarizeVideo, chatWithVideo } from "../api/summarize.js";
import {
  buildSubtitleBlob,
  safeDownloadName,
  triggerDownload,
} from "../utils/subtitleFormat.js";
import { downloadMindmapPng, downloadMindmapSvg } from "../utils/mindmapExport.js";

marked.use({ gfm: true, breaks: true });

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
const summaryStreaming = ref(false);
const mindmapLoading = ref(false);
const subtitleData = ref({ segments: [], has_subtitle: false });
const subtitleExpanded = ref(false);
const mindmapMarkdown = ref("");
const mindmapSvg = ref(null);
const mindmapContainer = ref(null);
let markmapInstance = null;
const isFullscreen = ref(false);
const showSubtitleDropdown = ref(false);
const subtitleDropdownRef = ref(null);
const subtitleFormats = [
  { key: "srt", label: "SRT 字幕", ext: "srt" },
  { key: "vtt", label: "VTT 字幕", ext: "vtt" },
  { key: "txt", label: "纯文本", ext: "txt" },
];
const exportHint = ref("");
const summaryContainer = ref(null);

const chatMessages = ref([]);
const chatInput = ref("");
const chatLoading = ref(false);
const chatContainer = ref(null);

const renderedSummary = ref("");

function finalizeSummaryMarkdown() {
  renderedSummary.value = renderMarkdown(summaryText.value);
}

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
    markmapInstance = Markmap.create(mindmapSvg.value, { autoFit: true }, root);
  } catch (e) {
    console.warn("思维导图渲染失败:", e);
  }
}

async function toggleFullscreen() {
  if (!mindmapContainer.value) return;
  try {
    if (!document.fullscreenElement) {
      const el = mindmapContainer.value;
      if (el.requestFullscreen) await el.requestFullscreen();
      else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    } else if (document.exitFullscreen) {
      await document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    }
  } catch (e) {
    console.warn("全屏不可用:", e);
  }
}

function onFullscreenChange() {
  isFullscreen.value = Boolean(document.fullscreenElement);
  nextTick(() => {
    if (markmapInstance) markmapInstance.fit();
  });
}

function handleClickOutside(e) {
  if (subtitleDropdownRef.value && !subtitleDropdownRef.value.contains(e.target)) {
    showSubtitleDropdown.value = false;
  }
}

function downloadSubtitle(format) {
  showSubtitleDropdown.value = false;
  const segments = subtitleData.value.segments;
  if (!segments?.length) return;
  const { content, ext } = buildSubtitleBlob(segments, format);
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  triggerDownload(blob, `${safeDownloadName(props.videoTitle)} - 字幕.${ext}`);
}

async function onDownloadPng() {
  exportHint.value = "";
  const ok = await downloadMindmapPng(
    mindmapSvg.value,
    `${safeDownloadName(props.videoTitle)} - 思维导图.png`,
  );
  if (!ok) exportHint.value = "PNG 导出失败，请改用 SVG";
}

function onDownloadSvg() {
  downloadMindmapSvg(
    mindmapSvg.value,
    `${safeDownloadName(props.videoTitle)} - 思维导图.svg`,
  );
}

function subtitleTypeLabel(type) {
  if (type === "manual") return "人工字幕";
  if (type === "description") return "视频文案";
  return "自动字幕";
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function scrollSummaryToBottom() {
  nextTick(() => {
    if (summaryContainer.value) {
      summaryContainer.value.scrollTop = summaryContainer.value.scrollHeight;
    }
  });
}

async function startSummarize() {
  loading.value = true;
  summaryText.value = "";
  summaryStreaming.value = false;
  mindmapLoading.value = false;
  renderedSummary.value = "";
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
        summaryStreaming.value = true;
        summaryText.value += data;
        scrollSummaryToBottom();
      },
      summary_done: () => {
        summaryStreaming.value = false;
        mindmapLoading.value = true;
        finalizeSummaryMarkdown();
      },
      mindmap: (data) => {
        mindmapLoading.value = false;
        try {
          const parsed = JSON.parse(data);
          mindmapMarkdown.value = parsed.markdown || "";
        } catch {
          /* ignore */
        }
      },
      done: () => {
        summaryStreaming.value = false;
        mindmapLoading.value = false;
        finalizeSummaryMarkdown();
        loading.value = false;
      },
      error: (data) => {
        summaryStreaming.value = false;
        mindmapLoading.value = false;
        loading.value = false;
        if (summaryText.value) {
          finalizeSummaryMarkdown();
        }
        try {
          const parsed = JSON.parse(data);
          emit("error", parsed.message || "总结失败");
        } catch {
          emit("error", `总结失败: ${data}`);
        }
      },
    });
  } catch (err) {
    summaryStreaming.value = false;
    mindmapLoading.value = false;
    loading.value = false;
    emit("error", `总结请求失败: ${err.message}`);
  }
}

async function sendQuestion() {
  const question = chatInput.value.trim();
  if (!question || chatLoading.value) return;

  chatInput.value = "";
  chatMessages.value.push({ role: "user", content: question });

  const aiIdx = chatMessages.value.length;
  chatMessages.value.push({ role: "assistant", content: "", loading: true });
  chatLoading.value = true;

  await nextTick();
  scrollChatToBottom();

  try {
    await chatWithVideo(props.videoUrl, question, subtitleData.value.full_text || "", {
      answer: (data) => {
        chatMessages.value[aiIdx].content += data;
        scrollChatToBottom();
      },
      done: () => {
        chatMessages.value[aiIdx].loading = false;
        chatLoading.value = false;
      },
      error: (data) => {
        chatMessages.value[aiIdx].loading = false;
        chatLoading.value = false;
        try {
          const parsed = JSON.parse(data);
          chatMessages.value[aiIdx].content = `❌ ${parsed.message || "回答失败"}`;
        } catch {
          chatMessages.value[aiIdx].content = "❌ 回答失败";
        }
      },
    });
  } catch (err) {
    chatMessages.value[aiIdx].loading = false;
    chatLoading.value = false;
    chatMessages.value[aiIdx].content = `❌ 请求失败: ${err.message}`;
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
  document.addEventListener("fullscreenchange", onFullscreenChange);
  document.addEventListener("webkitfullscreenchange", onFullscreenChange);
  document.addEventListener("click", handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener("fullscreenchange", onFullscreenChange);
  document.removeEventListener("webkitfullscreenchange", onFullscreenChange);
  document.removeEventListener("click", handleClickOutside);
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

.summary-output-wrap {
  max-height: 520px;
  overflow-y: auto;
}

.summary-stream-text,
.qa-stream-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.75;
  color: var(--ink);
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

.subtitle-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.subtitle-toggle {
  border: none;
  background: transparent;
  color: var(--blue);
  font-size: 12px;
  cursor: pointer;
}

.export-menu {
  position: relative;
}

.export-btn {
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  color: var(--ink);
  font-size: 12px;
  cursor: pointer;
}

.export-btn:focus-visible,
.export-item:focus-visible,
.subtitle-toggle:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

.export-pop {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  min-width: 160px;
  background: #fff;
  border: 1px solid var(--line-light);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(17, 24, 39, 0.08);
  padding: 6px;
  z-index: 5;
}

.export-item {
  width: 100%;
  display: flex;
  justify-content: space-between;
  border: none;
  background: transparent;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--ink);
}

.export-item:hover {
  background: var(--blue-soft);
}

.export-ext {
  color: var(--soft);
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

.mindmap-toolbar {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--line-light);
}

.mindmap-wrap.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 40;
  border-radius: 0;
  border: none;
  background: #fff;
}

.mindmap-wrap.fullscreen .mindmap-svg {
  min-height: calc(100vh - 56px);
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

.summary-prose :deep(h1) {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 1.5rem 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--blue-soft);
  color: var(--ink);
}

.summary-prose :deep(h2) {
  font-size: 1.125rem;
  font-weight: 700;
  margin: 1.25rem 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--line-light);
  color: var(--ink);
}

.summary-prose :deep(h3) {
  font-size: 1rem;
  font-weight: 600;
  margin: 1rem 0 0.5rem;
  color: var(--ink);
}

.summary-prose :deep(p),
.summary-prose :deep(li) {
  line-height: 1.75;
  margin-bottom: 0.5rem;
  color: var(--ink);
}

.summary-prose :deep(ul),
.summary-prose :deep(ol) {
  padding-left: 1.4rem;
  margin-bottom: 0.75rem;
}

.summary-prose :deep(li::marker) {
  color: var(--blue);
}

.summary-prose :deep(blockquote) {
  margin: 0.75rem 0;
  padding: 0.5rem 0.75rem;
  border-left: 3px solid var(--blue);
  background: var(--page);
  color: var(--muted);
}

.summary-prose :deep(code) {
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
  padding: 0.15em 0.4em;
  border-radius: 4px;
  background: var(--page);
  border: 1px solid var(--line-light);
  color: var(--ink);
}

.summary-prose :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  overflow-x: auto;
  margin: 0.75rem 0;
}

.summary-prose :deep(pre code) {
  background: none;
  border: none;
  padding: 0;
  color: inherit;
}

.summary-prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75rem 0;
  font-size: 13px;
}

.summary-prose :deep(th),
.summary-prose :deep(td) {
  border: 1px solid var(--line-light);
  padding: 8px 10px;
  text-align: left;
}

.summary-prose :deep(th) {
  background: var(--page);
  font-weight: 600;
}

.summary-prose :deep(a) {
  color: var(--blue);
}

.chat-prose :deep(h1),
.chat-prose :deep(h2),
.chat-prose :deep(h3) {
  font-size: 0.95rem;
  font-weight: 650;
  margin: 0.5rem 0 0.35rem;
}

.chat-prose :deep(p),
.chat-prose :deep(li) {
  line-height: 1.6;
  margin-bottom: 0.35rem;
}

.chat-prose :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-prose :deep(ul),
.chat-prose :deep(ol) {
  padding-left: 1.2rem;
  margin-bottom: 0.4rem;
}

.chat-prose :deep(li::marker) {
  color: var(--blue);
}

.chat-prose :deep(blockquote) {
  margin: 0.4rem 0;
  padding: 0.35rem 0.6rem;
  border-left: 3px solid var(--blue);
  background: var(--page);
  color: var(--muted);
}

.chat-prose :deep(code) {
  font-family: ui-monospace, monospace;
  font-size: 0.85em;
  padding: 0.1em 0.3em;
  border-radius: 4px;
  background: var(--page);
  border: 1px solid var(--line-light);
}

.chat-prose :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  overflow-x: auto;
  margin: 0.4rem 0;
}

.chat-prose :deep(pre code) {
  background: none;
  border: none;
  padding: 0;
  color: inherit;
}

.chat-prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.4rem 0;
  font-size: 12px;
}

.chat-prose :deep(th),
.chat-prose :deep(td) {
  border: 1px solid var(--line-light);
  padding: 6px 8px;
}

.chat-prose :deep(a) {
  color: var(--blue);
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
