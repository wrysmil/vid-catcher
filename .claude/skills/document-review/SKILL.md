---
name: document-review
description: 审查任何文档（规格、设计、计划）的完整性、清晰度和质量——特别是环境准备完整性时使用。触发词：review document, check document, audit spec, audit design, 审查文档, 检查文档, 文档审查
---

# 文档审查

系统化文档审查，附带按类型分类的审查规则。**环境准备**是设计和计划文档的首要检查项。

**核心原则：** 缺失环境配置带来的返工比缺失功能更严重。

## 使用时机

**始终使用：**
- 在批准规格、设计或实施计划之前
- 当用户要求审查、审计或检查文档时
- 头脑风暴之后、编写计划之前（设计文档的可选门禁）

**文档类型：**
- 需求/规格文档
- 架构/技术设计文档
- 实施计划
- 环境/部署配置文档

## 文档类型检测

阅读文档，然后匹配关键词（首次匹配即胜出；如果多个匹配，优先选择 design > plan > spec）：

| 文档信号 | 类型 | 加载规则文件 |
| --- | --- | --- |
| 需求, 用户故事, 功能, spec, requirement | 规格/需求 | `review-rules/spec.md` |
| 架构, 设计, 实现, API, 环境, 部署, design | 架构/技术设计 | `review-rules/design.md` |
| 计划, plan, 任务, 阶段, Phase, Task | 实施计划 | `review-rules/plan.md` |

检测完成后，**阅读**匹配的规则文件和 `checklists/review-checklist.md`。

## 审查流程

```
1. 检测文档类型
2. 加载 review-rules/<类型>.md + checklists/review-checklist.md
3. 对照规则审查（逐维度打分）
4. 输出报告（使用 artifact-templates/document-review.md）
5. 下一步：通过 → 继续；不通过 → 按优先级列出缺失项
```

## 输出格式

写入 `.ai-runtime-artifacts/reviews/YYYY-MM-DD-<主题>-document-review.md`，使用 `artifact-templates/document-review.md` 模板。

必需章节：
- 文档类型
- 已加载的规则
- 评分：完整性、清晰度、环境准备（如适用）
- 缺失项（按优先级排序）
- 具体改进建议
- 后续步骤

## 集成

| 阶段 | 技能 |
| --- | --- |
| 代码自测 / Leader 审查 | `requesting-code-review`（非本技能） |
| 实施 | `test-driven-development` + `writing-plans`（计划必须包含 Phase 1 环境准备） |
| 声明完成 | `verification-before-completion` |

本技能**仅审查文档**，不审查源代码。

## 红色警报 — 停止

- 跳过设计/计划文档的环境准备审查
- 只做表面审查而不列出具体缺失项
- 批准 Phase 1 不是环境准备的计划
- 用本技能审查代码（应使用 `requesting-code-review`）

## 防狡辩

| 借口 | 事实 |
| --- | --- |
| "环境配置很明显" | 必须明确列出依赖、环境变量、服务，否则不通过 |
| "测试后面再加" | 计划必须现在就包含测试策略 |
| "文档基本完整" | 逐维度打分；列出缺口 |
