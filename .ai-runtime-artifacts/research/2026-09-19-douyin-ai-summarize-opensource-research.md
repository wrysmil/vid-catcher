---
artifact: research-report
route: web-investigator
topic: douyin-ai-summarize-opensource
skills:
  - web-investigator
skills_evidence:
  - web-investigator@harness-kit/.agents/agents/web-investigator.md loaded
  - agent-browser: skipped（本次证据均为 GitHub / 官方文档静态页，WebSearch + WebFetch 已覆盖；无需交互截图）
source:
  - AGENTS.md
  - harness-kit/core/routing.md
  - 用户「对于抖音视频的AI总结好像目前还是不太行，请调研下有没有开源方案可以解决」
  - .ai-runtime-artifacts/specs/2026-09-19-video-summarize-spec.md
  - .ai-runtime-artifacts/verifications/2026-09-19-douyin-summarize-public-api-verification-lite.md
  - backend/app/summarizer.py
  - backend/app/douyin_service.py
created_at: 2026-09-19
---

# 抖音 AI 总结开源方案调研

## 调研目标

弄清 VidCatcher 抖音「AI 总结不太行」的根因，并盘点可落地的开源方案。约束对齐本项目：

- 只下载用户有权保存的公开内容；不写自定义提取器、不破解登录 / 签名 / Cookie
- 一期已有公开 API 解析（`iesdouyin iteminfo`）和 Command API 文本总结
- 学习向：优先「薄封装开源引擎」，不整仓引入第三方产品

## 当前实现为何不行

一期 spec（`2026-09-19-video-summarize-spec.md`）明确：**无字幕则报错，一期不做 Whisper；抖音不走专用字幕链路**。后来为了让精选页 / 短链能点总结，改成：

```
抖音 URL → parse_video(require_play_url=False) → 用 desc / description / title 当「字幕」
subtitle_type = "description"
```

公开 API `https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/` 返回的是元数据，不是口播稿。社区解析文章（[LivisSnack](https://livissnack.com/blog/douyin)）列出的核心字段只有 `desc`、`play_addr`、`cover`、`music.play_url`，**没有字幕轨**。

因此 LLM 总结的是创作者文案，不是视频内容。文案短、空、营销向时，总结必然空转。这不是 Command API 或 prompt 的问题，是**输入不是口播文本**。

补充：`music.play_url` 是背景乐，不能拿去 ASR。必须用视频 `play_addr`（项目里已有 `play_url`）。

## 搜索结果摘要

| # | 来源 | 标题 | 关键信息 |
|---|------|------|----------|
| 1 | GitHub | [modelscope/FunASR](https://github.com/modelscope/FunASR) | 中文 ASR 工具包（MIT）。SenseVoiceSmall 中文 CER ~7.8%，CPU 约 17× 实时；Whisper-large-v3 中文 CER ~20% |
| 2 | FunASR 文档 | [CLI / Tutorial](https://www.funasr.com/docs/command-line.html) | 本地文件 → SRT；默认 SenseVoice，可选 Paraformer + VAD + 标点 |
| 3 | GitHub | [QwenLM/Qwen3-ASR](https://github.com/qwenlm/qwen3-asr) | Apache-2.0；0.6B / 1.7B 可本地部署；官方称 1.7B 接近商用 API |
| 4 | GitHub | [bianshilong0604/doub-videoextract](https://github.com/bianshilong0604/doub-videoextract) | 抖音/B 站提取 + OpenAI 兼容总结；无字幕时可选 faster-whisper（默认关） |
| 5 | GitHub | [HYPERVAPOR/dysub](https://github.com/HYPERVAPOR/dysub) | 抖音链接 / 本地文件 → 自备 ASR API → SRT/VTT；推荐阿里云 `qwen3-asr-flash` |
| 6 | GitHub | [keepongo/video-summarizer](https://github.com/keepongo/video-summarizer) | 平台 API → yt-dlp 字幕 → Whisper；抖音元数据无 Cookie，口播仍靠 Whisper |
| 7 | PyPI | [lyrumu/vidsum](https://pypi.org/project/vidsum/) | B 站/抖音链接 → faster-whisper + 可配 LLM |
| 8 | GitHub | [majin72/skills-douyin-text-to-text](https://github.com/majin72/skills-douyin-text-to-text) | 下载无水印视频 + FunASR `paraformer-zh` 转写 |
| 9 | GitHub | [WEIFENG2333/VideoCaptioner](https://github.com/WEIFENG2333/VideoCaptioner) | 1.6 万星字幕全家桶；GPL-3.0，不适合当依赖整仓引入 |
| 10 | 文档 | [RapidVideOCR](https://swhl.github.io/RapidVideOCR/main/) | 硬字幕（烧录在画面上）OCR → SRT；适合「只有花字、几乎不口播」 |
| 11 | 社区 skill | [抖音文案提取](https://jindage.com/skills/douyin-extract-copywriter) | 部分视频有 `subtitle_infos` VTT/SRT，但来自需签名的 `aweme/v1/web/aweme/detail/` |

## 详细发现

### 1. 社区共识：抖音几乎没有可稳定用的官方字幕

B 站有公开 CC / AI 字幕 API，本项目已接。抖音没有对等的无签名字幕接口。

少数视频在 **网页详情接口** `aweme/v1/web/aweme/detail/` 的 `subtitle_infos` 里带 VTT/SRT。该接口通常要 Cookie、`msToken`、`X-Bogus` 等签名，社区下载器反复因此失效（例：[Evil0ctal#323](https://github.com/Evil0ctal/Douyin_TikTok_Download_API/issues/323)）。

**对本项目：不要接这条。** 违反「不写提取器 / 不绕过登录态 / 不破解签名」。即便接上，覆盖面也小，多数口播视频仍无轨。

能稳定拿到的只有：公开 API 的 **文案 + 无水印 play_url**。口播文本必须自己转写。

### 2. 开源「抖音总结」项目都是同一条管线

没有「输入链接就返回官方口播稿」的开源服务。能工作的项目都是：

```
解析链接拿播放地址 → 下载音视频 → ASR 转写 → LLM 总结
```

| 项目 | 许可 | 下载 | ASR | 总结 | 对本仓库 |
|------|------|------|-----|------|----------|
| [doub-videoextract](https://github.com/bianshilong0604/doub-videoextract) | MIT | scraper / yt-dlp / HTML | 可选 faster-whisper | OpenAI 兼容 | 模式最像；默认 ASR 关，关了就和我们现在一样只吃文案 |
| [keepongo/video-summarizer](https://github.com/keepongo/video-summarizer) | 未在 README 强调 | 公开 API + yt-dlp | Whisper 第三层 | Agent skill 出笔记 | 明确写了「无字幕就开 Whisper」 |
| [vidsum](https://pypi.org/project/vidsum/) | MIT | 自写 fetcher | faster-whisper | DeepSeek / GLM / Qwen / Ollama | 产品形态接近，但抖音仍靠本地下载+ASR |
| [dysub](https://github.com/HYPERVAPOR/dysub) | 开源 | 本地 + 抖音插件 | 用户自备 ASR API | 不做总结 | 只解决字幕；云端 Qwen ASR 常无句级时间戳 |
| [skills-douyin-text-to-text](https://github.com/majin72/skills-douyin-text-to-text) | 开源 | 无水印下载 | FunASR Paraformer | 不做总结 | 中文转写路径最贴近推荐 |
| [douyin-transcribe-lz](https://github.com/LiuZheng60/douyin-transcribe-lz) | 开源 | Playwright + API 兜底 | 本地 Whisper medium | 整理 Markdown | Playwright「登录墙」表述越界，只可参考 ASR 段 |
| [VideoCaptioner](https://github.com/WEIFENG2333/VideoCaptioner) | **GPL-3.0** | yt-dlp | faster-whisper / whisper.cpp / 必剪 | 可选 LLM | 功能全，病毒许可，勿整仓依赖 |
| [Douyin-full-stack-summarizer](https://github.com/skepty2333/Douyin-full-stack-summarizer) | 未核 | 未核 | Gemini / Whisper | 多模型流水线 | 企业微信 Bot + 多云密钥，过重 |

结论：**不要 vendor 这些仓库。** 复用管线即可。下载层我们已经有公开 API `play_url`；总结层已经有 `VideoSummarizer`。缺的只是中间的 ASR。

### 3. 开源 ASR 引擎对比（中文短视频）

抖音多数 15–180 秒，本机可接受「下载 + 转写 + 再调 LLM」。

| 引擎 | 许可 | 中文表现 | 速度 / 资源 | 时间戳 | 适配 |
|------|------|----------|-------------|--------|------|
| **FunASR SenseVoiceSmall** | 工具包 MIT，模型各异 | CER ~7.8%；普通话/粤语强 | CPU 约 17× 实时；ONNX 更轻 | 需配 VAD；FunASR CLI 可出 SRT | **首选**：短、中文、本机 CPU |
| **FunASR Paraformer-zh + fsmn-vad + ct-punc** | 同上 | 中文生产常用 | 非自回归，CPU 快 | 句级较好 | 与 majin72 skill 相同组合 |
| **Qwen3-ASR-0.6B / 1.7B** | Apache-2.0 | 官方称开源 SOTA，能抗 BGM/哼唱 | 0.6B 更轻；1.7B 更准、更吃显存 | 支持时间戳 / ForcedAligner | 质量上限高，依赖更重 |
| **faster-whisper** | MIT | 中文 CER ~20%；粤语常被认成普通话 | Python 集成简单；CPU 明显慢于 SenseVoice | 词级时间戳成熟 | 社区总结项目用得最多，中文不是最优 |
| **whisper.cpp** | MIT | 同 Whisper | 无 Python、Apple Silicon Metal | 有 | 适合独立 CLI，不优先嵌 FastAPI |
| **云端 qwen3-asr-flash**（DashScope） | 商用 API | 中文很好 | 同步 ≤5 分钟 / 10MB，正合短视频 | 常无句级时间戳（dysub 已踩坑） | 上线最快，但多一把密钥、音频出本机 |

FunASR 官方对比（[仓库 README](https://github.com/modelscope/FunASR)）：SenseVoiceSmall 中文 CER 7.81% vs Whisper-large-v3 20.02%，且 CPU 可跑。对「本机学习向、中文短视频」比 Whisper 更合适。一期 spec 写「不做 Whisper」是对的；现在要补的应是 **中文 ASR，不一定是 Whisper**。

### 4. 硬字幕 / 纯 BGM 视频：ASR 也会失败

大量抖音是「花字 + BGM、几乎不口播」。ASR 会转出歌词或空文本，总结依然差。

开源补法：

- [RapidVideOCR](https://github.com/SWHL/RapidVideOCR) + VideoSubFinder：抽硬字幕帧 → RapidOCR → SRT
- [video-copy-analyzer](https://github.com/ALBEDO-TABAI/video-copy-analyzer) skill：内嵌字幕 → OCR → FunASR 三层

这比 ASR 重，适合二期：ASR 文本过短或明显是歌词时再 OCR。

### 5. 和本仓库最贴的落地方案（调研建议，未实施）

不新写抖音提取器，只在已有 `play_url` 上加转写：

```
用户点 AI 总结（抖音）
  → 已有 parse_video() 拿 desc + play_url
  → 下载视频到临时目录（复用现有下载，勿用 music.play_url）
  → ffmpeg 抽音频（16k mono wav）
  → 本地 FunASR SenseVoice / Paraformer 出分段文本
  → 已有 VideoSummarizer（Command API）吃「文案 + 口播稿」
  → 现有 SSE 事件不变
```

分层建议：

| 层 | 输入 | 何时用 |
|----|------|--------|
| L0 文案 | `desc` | 只作标题/上下文，不再冒充字幕 |
| L1 口播 ASR | `play_url` 音轨 | 默认主路径 |
| L2 硬字幕 OCR | 视频画面 | ASR 过短 / 疑似纯 BGM 时（二期） |

明确不要做：

- 接 `aweme/detail` + `X-Bogus` 抢 `subtitle_infos`
- 把 VideoCaptioner / 各类 skill 整仓拷进仓库
- 多模态「看视频」大模型作主路径（重、贵、和现有文本总结架构不一致）

## 截图证据

| 描述 | 路径 |
|------|------|
| 无 | 本次为静态仓库/文档调研，未截交互页 |

## 结论

1. **根因**：抖音公开 API 没有口播字幕；当前用 `desc` 冒充字幕，所以总结不像视频内容。
2. **没有**「开源官方字幕接口」能单独修好；社区能跑通的都是 **下载 + ASR + LLM**。
3. **本仓库已有下载和 LLM**，缺的是中间转写。最省事且合规的做法：复用 `play_url`，接开源中文 ASR，不要再写提取器。
4. **引擎**：本机中文优先 **FunASR SenseVoiceSmall / Paraformer-zh**；要更高上限再看 **Qwen3-ASR-0.6B/1.7B**；**faster-whisper** 只当备选。云端 `qwen3-asr-flash` 适合先打通、不在乎音频出本机。
5. **硬字幕视频** 需要 OCR，单靠 ASR 不够，建议二期。

## 建议

若继续做，推荐「方案 A（本机 FunASR）」写 spec，而不是换 LLM 或改 prompt：

- **A（推荐）**：`play_url` → ffmpeg → FunASR → 现有总结。依赖变重（首次下模型、需 ffmpeg），中文质量最好，密钥不增加，符合学习向薄封装。
- **B（最快验证）**：同一下载链路，音频交给 DashScope `qwen3-asr-flash`。短视频时长匹配；多一把密钥，时间戳弱。
- **C（不推荐作默认）**：faster-whisper。集成简单，中文明显弱于 FunASR。
- **D（禁止）**：签名详情接口抢官方字幕轨。

## Next

- 认可方案 A 或 B → 说「写方案」或「出方案」，进入 spec（本轮只调研，未改代码）
- 先打通本机 ASR 可行性 → 说「补一发 SenseVoice 烟雾验证」，可对已有 `play_url` 做一次转写取证
- 仅存档 → 无需继续
