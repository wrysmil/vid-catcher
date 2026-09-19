---
artifact: contract
route: api-and-interface-design
skills:
  - api-and-interface-design
skills_evidence:
  - harness-kit/.agents/skills/api-and-interface-design/SKILL.md
source:
  - .ai-runtime-artifacts/specs/2026-09-19-summarize-export-polish-spec.md
  - .ai-runtime-artifacts/plans/2026-09-19-summarize-export-polish-plan.md
created_at: 2026-09-19
---

# 契约：总结 SSE token 编码（WU-01 ↔ WU-02）

跨 WU 唯一接口。两端必须同批上线，顺序：`subtitle` → `summary*` → `summary_done?` → `mindmap` → `done`。

## 事件与 payload

| event | data 线内容 | 前端解码 |
| --- | --- | --- |
| `subtitle` | `json.dumps(subtitle_object)` | `JSON.parse` 得对象 |
| `summary` | `json.dumps(token_str, ensure_ascii=False)` | `JSON.parse` 得**字符串**（含真实换行） |
| `answer` | 同上 | 同上 |
| `mindmap` | `json.dumps({"markdown": md})` | `JSON.parse` 得对象 |
| `error` | `json.dumps({"message": "..."})` | `JSON.parse` 得对象 |
| `done` / `summary_done` | 明文 `[DONE]` | 不当 token 解码 |

`token_str` 可以含 `\n`。编码后应出现在**单条** `data:` 中（JSON 转义），例如：

```text
event: summary
data: "概述\n\n- 要点"

```

## 前端解析（WU-02）

按 WHATWG：原始空行才 dispatch；多行 `data:` 用 `\n` 拼接；`summary`/`answer` 先 `JSON.parse`，失败回退原文。

## 不变

- 不新增 HTTP 路径
- `_sse()` 多行拆分逻辑可保留
- `subtitle` / `mindmap` / `error` 形状不变
