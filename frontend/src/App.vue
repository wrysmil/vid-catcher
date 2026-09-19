<template>
  <div class="site">
    <header class="nav">
      <a class="brand" href="#top">
        <span class="logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </span>
        <span class="brand-name">VidCatcher</span>
        <span class="brand-tag">视频捕手</span>
      </a>
      <nav class="nav-links">
        <a href="#features">功能特性</a>
        <a href="#plans">套餐价格</a>
        <a href="#platforms">支持平台</a>
      </nav>
      <button class="vip-btn" type="button" @click="showToast">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="m12 2 2.2 6.6H21l-5.4 4 2.1 6.4L12 15.8 6.3 19l2.1-6.4L3 8.6h6.8z" />
        </svg>
        开通 VIP
      </button>
    </header>

    <main>
      <section id="top" class="hero" :class="{ compact: hasResults }">
        <div class="hero-deco" aria-hidden="true">
          <span class="orb orb-a"></span>
          <span class="orb orb-b"></span>
        </div>
        <div class="hero-inner">
          <div v-if="showSlogan" class="badge"><span class="dot"></span> 支持 1800+ 平台，永久免费使用</div>
          <h1 v-if="showSlogan">视频捕手，<em>一键保存</em></h1>
          <p v-if="showSlogan" class="lead">
            粘贴视频链接，智能解析，支持多种清晰度下载。YouTube、Bilibili、抖音、TikTok...
            <br />
            随时随地，想下就下
          </p>

          <form class="capsule" @submit.prevent="parseAll">
            <div class="field">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.4-3.4" />
              </svg>
              <input
                v-model="rawInput"
                type="url"
                placeholder="https://www.youtube.com/watch?v=... 粘贴视频链接"
                autocomplete="off"
                :disabled="parsing"
              />
            </div>
            <button type="submit" :disabled="parsing || !hasInput">
              <svg v-if="parsing" class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none">
                <circle class="spinner-ring" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="spinner-arc" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.4-3.4" />
              </svg>
              {{ parsing ? "解析中..." : "解析视频" }}
            </button>
          </form>

          <div v-if="showSlogan" class="tries">
            试一试：
            <button type="button" @click="useDemo('https://www.youtube.com/watch?v=dQw4w9WgXcQ')">YouTube</button>
            <button type="button" @click="useDemo('https://www.bilibili.com/video/BV1GJ411x7h7')">Bilibili</button>
            <button type="button" @click="useDemo('https://x.com/elonmusk/status/1234567890')">Twitter/X</button>
          </div>
          <p v-if="error" class="error-line">{{ error }}</p>
        </div>
      </section>

      <section v-if="results.length" class="workspace">
        <div v-for="item in results" :key="item.key" class="workspace-row">
        <article class="result-card workspace-meta">
          <div class="result-head">
            <div class="thumb-wrap">
              <img
                v-if="hasRealThumb(item.thumbnail)"
                class="thumb"
                :src="item.thumbnail"
                :alt="item.title"
                @error="item.thumbnail = ''"
              />
              <div v-else class="thumb thumb-fallback" aria-hidden="true">
                <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                  <rect x="3" y="6" width="18" height="12" rx="2" />
                  <path d="M10 10v4l4-2z" fill="currentColor" stroke="none" />
                </svg>
                <span>{{ (item.title || "未命名视频").slice(0, 2) }}</span>
              </div>
              <span v-if="item.duration" class="duration">{{ formatClock(item.duration) }}</span>
            </div>
            <div class="result-meta">
              <h3>{{ item.title }}</h3>
              <div class="byline">
                <span class="uploader">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="8" r="3" />
                    <path d="M5 20a7 7 0 0 1 14 0" />
                  </svg>
                  {{ item.uploader || "未知作者" }}
                </span>
                <span class="platform">{{ displayPlatform(item.extractor) }}</span>
                <span v-if="item.viewCount" class="views">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
                  </svg>
                  {{ formatViews(item.viewCount) }}
                </span>
              </div>
              <p v-if="item.description" class="desc">{{ item.description }}</p>
            </div>
          </div>

          <div class="quality">
            <h4 class="quality-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
                <path d="M4 10v4M8 7v10M12 4v16M16 7v10M20 10v4" />
              </svg>
              选择清晰度和格式
            </h4>
            <div class="quality-grid">
              <button
                v-for="fmt in item.choices"
                :key="fmt.id"
                type="button"
                class="quality-card"
                :class="{ active: item.selected === fmt.id }"
                @click="item.selected = fmt.id"
              >
                <span class="quality-icon" aria-hidden="true">
                  <svg v-if="fmt.kind === 'audio'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 3v10.55A4 4 0 1 0 14 17V8h4V3h-6z" />
                  </svg>
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="6" width="18" height="12" rx="2" />
                    <path d="M10 10v4l4-2z" />
                  </svg>
                </span>
                <span class="quality-copy">
                  <strong>{{ fmt.title || fmt.label }}</strong>
                  <small>{{ fmt.subtitle || fmt.note }}</small>
                </span>
              </button>
            </div>
          </div>

          <div class="summary-row">
            <button
              type="button"
              class="summary-btn"
              :disabled="item.busy || item.summarizing"
              @click="restartSummary(item)"
            >
              {{ item.summarizing ? "总结中..." : "重新生成" }}
            </button>
          </div>

          <div class="download-row">
            <div class="progress-track" :class="{ show: item.task }">
              <div
                class="progress-fill"
                :style="{ width: `${Math.round((item.task?.progress || 0) * 100)}%` }"
              />
            </div>
            <div class="download-actions">
              <button class="cta" type="button" :disabled="item.busy" @click="downloadItem(item)">
                <svg v-if="item.busy && item.task?.status === 'downloading'" class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <circle class="spinner-ring" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="spinner-arc" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-1m-4-4-4 4m0 0-4-4m4 4V4" />
                </svg>
                {{ ctaLabel(item) }}
              </button>
              <span v-if="selectedLabel(item)" class="selected-hint">已选择：{{ selectedLabel(item) }}</span>
            </div>
          </div>
        </article>
        <div class="workspace-summary">
          <VideoSummary
            :key="item.summaryKey"
            :video-url="item.url"
            :video-title="item.title"
            @error="(msg) => (error = msg)"
            @loading-change="(on) => onSummaryLoading(item, on)"
          />
        </div>
        </div>
      </section>

      <section id="features" class="section">
        <h2>为什么选择 <span class="accent">VidCatcher</span></h2>
        <p class="section-sub">简单、快速、强大的视频下载体验</p>
        <div class="features">
          <article v-for="f in features" :key="f.title" class="feature-card">
            <span class="feature-icon" :class="f.tone">{{ f.icon }}</span>
            <h3>{{ f.title }}</h3>
            <p>{{ f.desc }}</p>
          </article>
        </div>
      </section>

      <section id="plans" class="section alt">
        <h2>选择适合你的方案</h2>
        <p class="section-sub">免费版满足日常使用，VIP 解锁全部高级功能</p>
        <div class="plans">
          <article class="plan">
            <h3>免费学习版</h3>
            <p class="plan-desc">满足基础下载需求</p>
            <div class="price"><strong>¥0</strong><small>/永久</small></div>
            <ul class="plan-list">
              <li v-for="t in freePlan" :key="t">{{ t }}</li>
            </ul>
            <button class="plan-btn" type="button" @click="showToast">当前方案</button>
          </article>
          <article class="plan vip">
            <span class="vip-badge">🔥 推荐</span>
            <h3>VIP 高级版</h3>
            <p class="plan-desc">解锁全部功能，无限制使用</p>
            <div class="price"><strong>¥9.9</strong><small>/月</small></div>
            <ul class="plan-list">
              <li v-for="t in vipPlan" :key="t">{{ t }}</li>
            </ul>
            <button class="plan-btn light" type="button" @click="showToast">开通 VIP</button>
          </article>
        </div>
      </section>

      <section id="platforms" class="section">
        <h2>支持全球 <span class="accent">1800+</span> 平台</h2>
        <p class="section-sub">几乎覆盖所有主流视频、音频、社交媒体平台</p>
        <div class="platforms">
          <span v-for="p in platforms" :key="p.name" class="platform-chip">{{ p.icon }} {{ p.name }}</span>
        </div>
      </section>

      <footer class="footer">
        <div class="footer-brand">
          <span class="logo small">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </span>
          <span>VidCatcher</span>
        </div>
        <p class="footer-note">
          学习项目，引擎是开源的 yt-dlp。请尊重版权，只保存你有权下载的内容。<br />
          不要拿去对抗平台风控，也不要公开当盗链站用。
        </p>
        <p class="footer-copy">© {{ new Date().getFullYear() }} VidCatcher</p>
      </footer>
    </main>
    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
import VideoSummary from "./components/VideoSummary.vue";

const rawInput = ref("");
const parsing = ref(false);
const error = ref("");
const results = ref([]);
const toast = ref("");
const timers = new Set();
const presentMode = ref(false);

const hasInput = computed(() => rawInput.value.trim().length > 0);
const hasResults = computed(() => results.value.length > 0);
const showSlogan = computed(() => !hasResults.value || presentMode.value);

let enterCount = 0;
let enterTimer = null;

function onGlobalKeydown(event) {
  if (event.key !== "Enter") return;
  const target = event.target;
  if (target instanceof Element && target.matches("input, textarea, [contenteditable]")) {
    return;
  }
  enterCount += 1;
  clearTimeout(enterTimer);
  if (enterCount >= 3) {
    presentMode.value = !presentMode.value;
    enterCount = 0;
    return;
  }
  enterTimer = setTimeout(() => {
    enterCount = 0;
  }, 800);
}

const features = [
  { icon: "🌐", tone: "blue", title: "支持 1800+ 平台", desc: "YouTube、Bilibili、抖音、TikTok、Twitter 等全球主流平台" },
  { icon: "⚡", tone: "amber", title: "极速解析下载", desc: "智能解析视频链接，自动匹配最优下载方式，速度快人一步" },
  { icon: "📱", tone: "green", title: "手机也能用", desc: "完美适配手机浏览器，随时随地，想下就下，无需安装 App" },
  { icon: "🎬", tone: "purple", title: "多种清晰度", desc: "支持从 360p 到 4K 多种清晰度选择，满足不同场景需求" },
  { icon: "🤖", tone: "blue", title: "AI 视频总结", desc: "自动生成摘要、字幕、思维导图，支持针对视频内容提问" },
];

const freePlan = [
  "解析 + 选清晰度 + 下载到此设备",
  "最高支持 720p 清晰度",
  "支持 1800+ 平台",
  "无账号、无数据库",
];

const vipPlan = [
  "无限次下载，无任何限制",
  "批量下载，一键搞定",
  "字幕下载与翻译",
  "AI 视频内容总结",
];

const platforms = [
  { icon: "▶️", name: "YouTube" },
  { icon: "📺", name: "Bilibili" },
  { icon: "🎵", name: "抖音 / TikTok" },
  { icon: "🐦", name: "Twitter / X" },
  { icon: "📷", name: "Instagram" },
  { icon: "📘", name: "Facebook" },
  { icon: "🎬", name: "Vimeo" },
  { icon: "🎧", name: "SoundCloud" },
];

function useDemo(url) {
  rawInput.value = url;
}

// 后端有时会返回一张 1x1 的透明占位图（B 站 API 在未拿到真实 cover 时返回
// https://i0.hdslb.com/bfs/archive/transparent.png）。这种 URL 浏览器能正常加载，
// 但渲染出来是透明的，肉眼看就像没图。这里在前端统一识别成「无封面」。
function hasRealThumb(url) {
  if (!url) return false;
  const trimmed = String(url).trim();
  // 后端代理路径直接放行；B 站老 transparent 占位继续过滤。
  if (trimmed.startsWith("/api/thumbnail")) return true;
  const lower = trimmed.toLowerCase();
  if (!lower.startsWith("http")) return false;
  if (lower.endsWith("/transparent.png")) return false;
  if (lower.includes("bfs/archive/transparent")) return false;
  return true;
}

async function parseAll() {
  error.value = "";
  const urls = [...new Set(rawInput.value.split(/[\s,，]+/).map((s) => s.trim()).filter(Boolean))];
  if (!urls.length) {
    error.value = "先粘贴一条视频链接";
    return;
  }
  parsing.value = true;
  try {
    const next = [];
    for (const url of urls) {
      const res = await fetch("/api/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "解析失败");
      const choices = data.choices?.length
        ? data.choices
        : [...(data.presets || []), ...(data.formats || [])].slice(0, 8);
      next.push({
        key: `${url}-${Date.now()}`,
        url,
        title: data.title,
        thumbnail: data.thumbnail,
        duration: data.duration,
        extractor: data.extractor,
        uploader: data.uploader,
        viewCount: data.view_count,
        description: data.description,
        choices,
        selected: choices[0]?.id || "bv*+ba/b",
        busy: false,
        task: null,
        summaryKey: Date.now() + next.length,
        summarizing: false,
      });
    }
    presentMode.value = false;
    results.value = next;
  } catch (err) {
    error.value = err.message;
  } finally {
    parsing.value = false;
  }
}

async function downloadItem(item) {
  item.busy = true;
  item.task = { progress: 0, status: "queued" };
  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: item.url, format_id: item.selected }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "无法开始下载");
    item.task = data;
    pollTask(item, data.id);
  } catch (err) {
    item.busy = false;
    error.value = err.message;
  }
}

function pollTask(item, taskId) {
  const timer = setInterval(async () => {
    try {
      const res = await fetch(`/api/tasks/${taskId}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "任务丢失");
      item.task = data;
      if (data.status === "finished" && data.ready) {
        clearInterval(timer);
        timers.delete(timer);
        item.busy = false;
        window.location.assign(`/api/tasks/${taskId}/file`);
      } else if (data.status === "error") {
        clearInterval(timer);
        timers.delete(timer);
        item.busy = false;
        error.value = data.error || "下载失败";
      }
    } catch (err) {
      clearInterval(timer);
      timers.delete(timer);
      item.busy = false;
      error.value = err.message;
    }
  }, 1200);
  timers.add(timer);
}

function selectedLabel(item) {
  const fmt = item.choices.find((c) => c.id === item.selected);
  return fmt ? fmt.title || fmt.label || "" : "";
}

function ctaLabel(item) {
  if (!item.task) return "立即下载";
  if (item.task.status === "downloading") return `下载中 ${Math.round((item.task.progress || 0) * 100)}%`;
  if (item.task.status === "queued") return "排队中...";
  if (item.task.status === "finished") return "已开始保存";
  return "立即下载";
}

function formatClock(seconds) {
  const total = Math.max(0, Math.round(Number(seconds) || 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatViews(count) {
  const n = Number(count);
  if (!Number.isFinite(n)) return "";
  if (n >= 100000000) return `${(n / 100000000).toFixed(1).replace(/\.0$/, "")}亿`;
  if (n >= 10000) return `${(n / 10000).toFixed(n >= 100000 ? 0 : 1).replace(/\.0$/, "")}万`;
  return n.toLocaleString("en-US");
}

function displayPlatform(extractor) {
  const key = String(extractor || "").toLowerCase();
  if (key.includes("bili")) return "Bilibili";
  if (key.includes("youtube")) return "YouTube";
  if (key.includes("douyin")) return "抖音";
  if (key.includes("tiktok")) return "TikTok";
  if (key.includes("twitter") || key === "x") return "Twitter/X";
  return extractor || "未知平台";
}

function restartSummary(item) {
  if (item.summarizing) return;
  item.summaryKey += 1;
}

function onSummaryLoading(item, isLoading) {
  item.summarizing = Boolean(isLoading);
}

function showToast() {
  toast.value = "学习版即将开放，先把下载用爽";
  setTimeout(() => {
    toast.value = "";
  }, 2200);
}

onMounted(() => {
  document.addEventListener("keydown", onGlobalKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", onGlobalKeydown);
  clearTimeout(enterTimer);
  timers.forEach(clearInterval);
});
</script>
