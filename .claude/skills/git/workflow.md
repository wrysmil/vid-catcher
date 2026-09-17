# 组织 Git 工作流（主干 + 多环境 + 功能分支）

本文档描述本技能默认遵循的分支模型与合流顺序；与通用 Git 命令说明见 `commands.md`、`advanced.md`。

## 1. 目标（与 Git 操作相关部分）

- 开发 / 测试 / 生产通过分支隔离，权限降低误合并与误发布风险。
- 支持大型功能、中型功能、临时验证并行；支持紧急缺陷修复与提测版本线。
- 提交历史可追溯、可审计：约定式提交 + 合并请求（MR/PR）。

## 2. 分支模型总览

```
生产事故 ──► bugfix/* ──────────────────────────────┐
                                                     ▼
main (生产) ◄──── test/v* (提测) ◄──── develop (开发集成)
                                                     ▲
                                           ┌─────────┼─────────┐
                                           │         │         │
                                        feature/*  task/*   temp/*
                                        (大型等)  (中型等) (临时/探索)
```

- 图中 **`test/v*`** 表示提测版本线（如 `test/v2.4.0`）；若团队另有一条长期命名为 `test` 的测试集成分支，职责与保护规则以**远端配置**为准，勿与某次提测线混淆。
- **模式**：主干稳定 + 多环境长期分支 + 功能类临时分支 + 热修复分支。
- **长期分支（受保护、不直接在上面长期写代码）**：`main`、`test`（若团队用单条测试集成分支）、`develop`（开发集成）。具体以远程仓库保护规则为准。
- **临时分支（用完即删）**：`feature/*`、`task/*`、`temp/*`、`bugfix/*`、`test/v*` 等。

## 3. 版本号 Va.b.c.d（与分支类型的对应）

- **a**：大版本，通常重大更新才升，由人为决定。
- **b**：功能版本，与 **feature / task** 等正式功能迭代相关时递增。
- **c**：临时需求维度，与 **temp** 相关时递增。
- **d**：缺陷修复，与 **bugfix** 相关时递增。

（具体递增策略以发布负责人为准；此处记录「版本位与分支语义」的对应关系。）**勿与 npm/package.json 等常见的 SemVer（主.次.补丁）自动等同**——本组织四位版本号的含义以发布负责人解释为准。

## 4. 分支命名

- **推荐形式**：`<类型>/<模块名或版本信息>-<简短英文或拼音描述>`，用连字符分隔。
- **示例**：
  - `feature/user-center-rbac`
  - `task/user-avatar-upload`
  - `temp/try-redis-cache`
  - `bugfix/v2.3.12-login-token-expire`
  - `test/v2.4.0`
- **禁忌（示例）**：含义模糊、用人名、全大写、用日期当路径、过长无结构。

## 5. 长期分支职责

| 分支 | 含义 | 要求摘要 |
|------|------|----------|
| `main` | 生产环境代码 | 禁止直接提交；禁止个人随意 push；仅经 MR/PR，且经评审与测试验证后合入。 |
| `test` | 测试环境集成 | 用于联调 / 验收；提测线如 `test/v*` 上**只修缺陷，不加新功能**（除非团队另有约定）。 |
| `develop` | 开发集成 | 日常集成分支；**不要**长期在 `develop` 上直接开发，应在 `feature`/`task`/`temp` 上开发后 MR 合入。 |

## 6. 临时分支：来源与目标

| 类型 | 自何创建 | 合并目标 | 说明 |
|------|----------|----------|------|
| `feature/*` | `develop` | `develop` | 大型模块、跨人协作；可有子分支；子分支定期合回主 feature；主 feature 定期同步 `develop`（如每周）。 |
| `task/*` | `develop` | `develop` | 常规需求；小步提交；提 MR 前同步 `origin/develop`（推荐 `rebase`）。 |
| `temp/*` | `develop` | `develop` 或废弃删除 | 短周期验证；验证通过可转正式 `feature`/`task`；放弃则删分支。 |
| `bugfix/*` | **`main`** | **`main` 与 `develop` 须同时合入** | 热修复；禁止只修 `main` 不回 `develop`，否则后续发版会带回缺陷。 |
| `test/v…` | `develop` | 测试通过后进 `main`，修复需回合 `develop` | 见下文「测试环境流程」。 |

## 7. 典型流程（命令级摘要）

### 7.1 feature（大型，可含子分支）

1. `git checkout develop` → `git pull` → `git checkout -b feature/…`
2. 子分支示例：`feature/xxx-frontend`、`feature/xxx-backend`；定期将子分支合并回主 `feature/xxx`。
3. 主 feature 定期执行 `git merge origin/develop` 或 `git rebase origin/develop`（团队约定为准）。
4. 完成后 **MR → `develop`**，通过评审与 CI。

### 7.2 task

1. 从 `develop` 建 `task/…`。
2. 完成前：`git fetch origin` → `git rebase origin/develop`（或 `merge`）。
3. **MR → `develop`**。

### 7.3 temp

1. 从 `develop` 建 `temp/…`。
2. 保留则 MR → `develop`；放弃则本地与远程删分支。

### 7.4 bugfix（紧急）

1. `git checkout main` → `git pull` → `git checkout -b bugfix/…`
2. 修复并提交后：**分别 MR 到 `main` 与 `develop`**（顺序与权限以团队为准）。
3. 在 `main` 上打标签（如 `v2.3.12`），推送标签。
4. 删除 `bugfix` 分支。

### 7.5 测试分支 test/v*

1. 从 `develop` 建 `test/v2.4.0` 等，部署测试环境。
2. 该阶段**以修 bug 为主**，避免塞新功能。
3. 测试通过后 **MR → `main`**，打版本标签。
4. 将 `test` 上的修复 **回合到 `develop`**（`merge` 等），再删除 `test` 分支。

## 8. 提交信息（Angular）

**约定式提交的格式、类型、范围、正反例以 `SKILL.md` 中「提交规范（Angular）」为唯一详述**，本文不重复罗列，避免双处维护不一致。

## 9. 合并请求（MR/PR）要点

填写说明（变更内容、关联工单、测试方式、截图、是否破坏性变更等）与 **合并前后动作**（提交前对齐 `develop`、合并后删除分支）见 **`SKILL.md`** 中「核心规则」「推送与强推」「分支卫生」及下文本仓库 §15 检查清单；此处不重复。

## 10. 受保护分支上的「回滚」

- **`main` / `develop` 上禁止用 `git reset --hard` 作为协作回滚手段**，应使用 **`git revert`**（对合并提交用 `git revert -m 1 <merge-sha>`）。
- 误合并进 `develop` 的修复示例：`git checkout develop` → `git revert -m 1 <merge-commit>` → `git push`。

个人功能分支、本地未推送的整理仍可使用 `reset`/`rebase`（注意勿强推公共分支）。

## 11. 多 feature 有依赖时

- **方案 A**：`feature/B` 基于 `feature/A` 创建；`A` 合入 `develop` 后，`B` 再 `rebase develop`。
- **方案 B**：建集成分支 `feature/integration-…`，合并 `A`、`B` 验证后，再分别 MR 到 `develop`。

## 12. 前后端并行（非 Git，但与提交有关）

- 接口未就绪时可用 Mock；可在提交信息中标注 `[mock]` 或对接真实接口的说明。

## 13. 团队 `.gitignore` 基础模板

以下为常见栈的**起点**，按项目裁剪；完整列表以团队仓库模板为准。

```
# 通用
.DS_Store
Thumbs.db
*.log
*.tmp
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# 前端（示例）
node_modules/
dist/
.nuxt/
.next/
*.local

# Java（示例）
target/
*.class
*.jar
*.war
build/
.gradle/
out/

# Python（示例）
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
venv/
.venv/

# 敏感信息（严禁提交）
*.pem
*.key
*_secret*
credentials.json
```

## 14. 敏感信息已入库后的处置（原则）

若密钥、令牌等**已随提交推送到远端**，仅在本机 `git revert` 或改写历史**不能保证**未泄露（他人可能已拉取、镜像或 CI 已打印）。

1. **立即轮换**受影响凭据（API Key、密码、证书等），按安全流程作废旧值。  
2. **通知**安全或平台管理员，按 Git 托管平台流程评估是否需从历史中清除敏感 blob（通常需管理员权限与团队决策）。  
3. **禁止**在公开渠道粘贴含密钥的提交哈希或完整 diff。

详细命令与平台差异以各托管方文档为准；本技能只强调流程优先级：**轮换优先于「只删提交」**。

## 15. 执行检查清单（成员）

- 不直接向 `main`、`develop` 推送个人开发提交；走 MR。
- 不在公共受保护分支上使用 `git push --force`。
- 每次提交符合消息规范；MR 前先同步 `develop`。
- MR 合并后删除临时分支。
- 密钥、大文件（团队约定如 **大于约 10MB** 用 LFS 或外部存储）不直接入库。
- 冲突解决后确保能构建、测试通过。
