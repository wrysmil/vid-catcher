<template>
  <div class="site">
    <header class="nav">
      <a class="brand" href="#top">
        <span class="logo">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z" />
          </svg>
        </span>
        SaveAny
        <small>万能视频下载</small>
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

    <section id="top" class="hero">
      <div class="badge"><span class="dot"></span> 支持 18000+ 平台，永久免费使用</div>
      <h1>万能视频下载器，<em>一键保存</em></h1>
      <p class="lead">
        粘贴视频链接，智能解析，支持多种清晰度下载。YouTube、Bilibili、抖音、TikTok...
        <br />
        随时随地，想下就下
      </p>

      <form class="capsule" @submit.prevent="parseAll">
        <div class="field">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10 13a5 5 0 0 0 7.07 0l2.12-2.12a5 5 0 0 0-7.07-7.07L10.7 5.24" />
            <path d="M14 11a5 5 0 0 0-7.07 0L4.81 13.12a5 5 0 1 0 7.07 7.07L13.3 18.76" />
          </svg>
          <input
            v-model="rawInput"
            type="url"
            placeholder="https://www.youtube.com/watch?v=... 粘贴视频链接"
            autocomplete="off"
            :disabled="parsing"
          />
        </div>
        <button type="submit" :disabled="parsing">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.4-3.4" />
          </svg>
          {{ parsing ? "解析中" : "解析视频" }}
        </button>
      </form>

      <div class="tries">
        试一试：
        <button type="button" @click="useDemo('https://www.youtube.com/watch?v=YE7VzlLtp-4')">YouTube</button>
        <button type="button" @click="useDemo('https://www.bilibili.com/video/BV1xx411c7mD')">Bilibili</button>
        <button type="button" @click="useDemo('https://x.com/i/status/20')">Twitter/X</button>
      </div>
      <p v-if="error" class="error-line">{{ error }}</p>
    </section>

    <section v-if="results.length" class="results">
      <article v-for="item in results" :key="item.key" class="result-card">
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
          <div class="quality-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
              <path d="M4 10v4M8 7v10M12 4v16M16 7v10M20 10v4" />
            </svg>
            选择清晰度和格式
          </div>
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

        <div v-if="item.task" class="progress">
          <span :style="{ width: `${Math.round((item.task.progress || 0) * 100)}%` }" />
        </div>
        <button class="cta" type="button" :disabled="item.busy" @click="downloadItem(item)">
          {{ ctaLabel(item) }}
        </button>
      </article>
    </section>

    <section id="features" class="why">
      <h2>为什么选择 SaveAny</h2>
      <p>简单、快速、强大的视频下载体验</p>
      <div class="features">
        <article class="feature">
          <h3>一键解析</h3>
          <p>粘贴链接即可读出封面、时长和清晰度，不用翻平台设置。</p>
        </article>
        <article class="feature">
          <h3>自选画质</h3>
          <p>最高清、1080p、720p 或只要音频，手机流量也能控。</p>
        </article>
        <article class="feature">
          <h3>随时随地</h3>
          <p>浏览器打开就能下，电脑和手机同一套页面。</p>
        </article>
      </div>
    </section>

    <section id="plans" class="why">
      <h2>套餐价格</h2>
      <p>学习版先免费用下载，增值能力稍后开放</p>
      <div class="plans">
        <article class="plan">
          <h3>免费学习版</h3>
          <p>解析 + 选清晰度 + 下载到此设备。无账号、无数据库。</p>
        </article>
        <article class="plan hot">
          <h3>VIP 预告</h3>
          <p>视频总结、字幕翻译、无限批量，先占位，不接真实支付。</p>
          <button type="button" @click="showToast">开通 VIP</button>
        </article>
      </div>
    </section>

    <section id="platforms" class="why">
      <h2>支持平台</h2>
      <p>能力来自 yt-dlp，站点改版时升级引擎即可</p>
      <div class="platforms">
        <article class="platform-card"><h3>YouTube</h3><p>讲座、公开课</p></article>
        <article class="platform-card"><h3>Bilibili</h3><p>课堂回放</p></article>
        <article class="platform-card"><h3>抖音 / TikTok</h3><p>短视频备忘</p></article>
        <article class="platform-card"><h3>Twitter / X</h3><p>媒体贴</p></article>
      </div>
    </section>

    <footer class="footer">
      学习项目，引擎是开源的 yt-dlp。请尊重版权，只保存你有权下载的内容。<br />
      不要拿去对抗平台风控，也不要公开当盗链站用。
    </footer>
    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from "vue";

const rawInput = ref("");
const parsing = ref(false);
const error = ref("");
const results = ref([]);
const toast = ref("");
const timers = new Set();

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
      });
    }
    results.value = [...next, ...results.value];
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

function ctaLabel(item) {
  if (!item.task) return "下载到此设备";
  if (item.task.status === "downloading") return `下载中 ${Math.round((item.task.progress || 0) * 100)}%`;
  if (item.task.status === "queued") return "排队中";
  if (item.task.status === "finished") return "已开始保存";
  return "下载到此设备";
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
  if (n >= 10000) return `${(n / 10000).toFixed(n >= 100000 ? 0 : 1).replace(/\.0$/, "")}万`;
  return n.toLocaleString("en-US");
}

function displayPlatform(extractor) {
  const key = String(extractor || "").toLowerCase();
  if (key.includes("bili")) return "BiliBili";
  if (key.includes("youtube")) return "YouTube";
  if (key.includes("tiktok") || key.includes("douyin")) return "TikTok";
  if (key.includes("twitter") || key === "x") return "Twitter/X";
  return extractor || "未知平台";
}

function showToast() {
  toast.value = "学习版即将开放，先把下载用爽";
  setTimeout(() => {
    toast.value = "";
  }, 2200);
}

onBeforeUnmount(() => {
  timers.forEach(clearInterval);
});
</script>
