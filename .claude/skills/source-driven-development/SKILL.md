---
name: source-driven-development
description: Grounds every implementation decision in project documentation AND official framework docs. Use before writing any code — check project artifacts first, then verify framework APIs. Prevents "retraining from scratch" each session.
---

# Source-Driven Development

## Overview

Every implementation decision must be backed by two layers of documentation:

1. **Project-internal docs** (`.ai-runtime-artifacts/` — specs, plans, decisions, research, contracts): What has already been designed, decided, and planned for this project. Reading these first ensures continuity across sessions — you don't "re-train from scratch" each time.
2. **External framework docs** (official documentation for React, Python, etc.): The correct API signatures, patterns, and best practices for the current version. Training data goes stale; docs don't lie.

**Rule: read project docs BEFORE writing code.** Don't implement from memory of "what the codebase probably looks like" — check what's actually been designed. Don't implement framework code from memory of "how the API probably works" — verify against the current version's documentation.

## When to Use

- **Any implementation task** — before writing code, check `.ai-runtime-artifacts/` for related specs/plans/decisions
- The user wants code that follows current best practices for a given framework
- Building boilerplate, starter code, or patterns that will be copied across a project
- The user explicitly asks for documented, verified, or "correct" implementation
- Implementing features where the framework's recommended approach matters (forms, routing, data fetching, state management, auth)
- Reviewing or improving code that uses framework-specific patterns
- **Continuing work from a previous session** — specs/plans are the bridge between sessions; read them first

**When NOT to use:**

- Correctness does not depend on a specific version (renaming variables, fixing typos, moving files)
- Pure logic that works the same across all versions (loops, conditionals, data structures)
- The user explicitly wants speed over verification ("just do it quickly") — but Step 0 (project docs) still applies unless this is a Tier 0 mechanical fix

## The Process

```
CHECK ARTIFACTS ──→ DETECT ──→ FETCH ──→ IMPLEMENT ──→ CITE
      │               │          │           │            │
      ▼               ▼          ▼           ▼            ▼
  What has        What       Get the    Follow the   Show your
  already been    stack?     relevant   documented   sources
  designed?                  docs       patterns
```

### Step 0: Check Project Documentation (MANDATORY — do not skip)

**Before writing a single line of code**, check what the project already knows about this task. This is the bridge between sessions — it prevents "retraining from scratch" every time.

#### 0.1 Scan `.ai-runtime-artifacts/` for related artifacts

```
.ai-runtime-artifacts/specs/       → 方案、需求澄清、意图说明
.ai-runtime-artifacts/plans/       → 实施计划、dispatch 调度
.ai-runtime-artifacts/decisions/   → 架构决策记录
.ai-runtime-artifacts/contracts/   → 接口契约（跨 WU 依赖）
.ai-runtime-artifacts/research/    → 调研结果
.ai-runtime-artifacts/stack/       → 技术栈检测结果（已生成时复用）
.ai-runtime-artifacts/verifications/ → 历史验证结果
.ai-runtime-artifacts/reviews/     → 历史审查结果
```

**How to scan:**
- Use `find` or `ls` to list artifacts related to your task topic
- If task is about "user authentication", look for files with `auth`, `login`, `user` in the name
- If the user references a specific feature, search for that feature name

#### 0.2 Read the most relevant artifacts

From the scan results, read the 1–3 most relevant files:

```
FOUND:
- .ai-runtime-artifacts/specs/2026-06-15-user-auth-spec.md  ← READ FIRST
- .ai-runtime-artifacts/plans/2026-06-16-user-auth-plan.md  ← READ SECOND
- .ai-runtime-artifacts/decisions/2026-06-17-jwt-vs-session.md ← READ IF RELEVANT
```

#### 0.3 Load project context files

```
project.profile.md   → 技术栈、命令、公约、边界、禁区
context-map.md       → 模块索引、关键文件位置、读码优先级
```

#### 0.4 State what you found

Explicitly tell the user what documentation you're building on:

```
PROJECT DOCS FOUND:
- Spec: 2026-06-15-user-auth-spec.md (JWT-based auth, /api/auth/login)
- Plan: 2026-06-16-user-auth-plan.md (WU-01 backend, WU-02 frontend)
- Decision: JWT over session cookies (2026-06-17)
- No conflicts between existing docs.

→ Proceeding with implementation based on the above.
```

If NO related artifacts exist, state that explicitly:

```
NO RELATED PROJECT DOCS FOUND in .ai-runtime-artifacts/.
→ This appears to be a new area. Will proceed with framework docs + project conventions.
→ Consider running brainstorming → writing-plans first if scope is non-trivial.
```

**If artifacts conflict or are outdated**, surface the discrepancy BEFORE coding:

```
ARTIFACT CONFLICT:
Spec says "Use session cookies for auth" (2026-06-15),
but plan says "Use JWT Bearer tokens" (2026-06-16).
→ Which is the current approach?
```

#### 0.5 Decision gate

| Scenario | Action |
|---|---|
| Related spec + plan exist, both approved | Read both → implement based on plan |
| Spec exists, no plan | Read spec → suggest writing plan if multi-step |
| No artifacts, non-trivial task | Flag → suggest brainstorming before coding |
| No artifacts, Tier 0 mechanical fix | Skip to Step 1, note "no related artifacts" |
| Artifacts conflict | Surface conflict → wait for user resolution |

### Step 1: Detect Stack and Versions

Read the project's dependency file to identify exact versions:

```
package.json    → Node/React/Vue/Angular/Svelte
composer.json   → PHP/Symfony/Laravel
requirements.txt / pyproject.toml → Python/Django/Flask
go.mod          → Go
Cargo.toml      → Rust
Gemfile         → Ruby/Rails
```

State what you found explicitly:

```
STACK DETECTED:
- React 19.1.0 (from package.json)
- Vite 6.2.0
- Tailwind CSS 4.0.3
→ Fetching official docs for the relevant patterns.
```

If versions are missing or ambiguous, **ask the user**. Don't guess — the version determines which patterns are correct.

### Step 2: Fetch Official Documentation

Fetch the specific documentation page for the feature you're implementing. Not the homepage, not the full docs — the relevant page.

**Source hierarchy (in order of authority):**

| Priority | Source | Example |
|----------|--------|---------|
| 1 | Official documentation | react.dev, docs.djangoproject.com, symfony.com/doc |
| 2 | Official blog / changelog | react.dev/blog, nextjs.org/blog |
| 3 | Web standards references | MDN, web.dev, html.spec.whatwg.org |
| 4 | Browser/runtime compatibility | caniuse.com, node.green |

**Not authoritative — never cite as primary sources:**

- Stack Overflow answers
- Blog posts or tutorials (even popular ones)
- AI-generated documentation or summaries
- Your own training data (that is the whole point — verify it)

**Be precise with what you fetch:**

```
BAD:  Fetch the React homepage
GOOD: Fetch react.dev/reference/react/useActionState

BAD:  Search "django authentication best practices"
GOOD: Fetch docs.djangoproject.com/en/6.0/topics/auth/
```

After fetching, extract the key patterns and note any deprecation warnings or migration guidance.

When official sources conflict with each other (e.g. a migration guide contradicts the API reference), surface the discrepancy to the user and verify which pattern actually works against the detected version.

### Step 3: Implement Following Documented Patterns

Write code that matches what the documentation shows:

- Use the API signatures from the docs, not from memory
- If the docs show a new way to do something, use the new way
- If the docs deprecate a pattern, don't use the deprecated version
- If the docs don't cover something, flag it as unverified

**When docs conflict with existing project code:**

```
CONFLICT DETECTED:
The existing codebase uses useState for form loading state,
but React 19 docs recommend useActionState for this pattern.
(Source: react.dev/reference/react/useActionState)

Options:
A) Use the modern pattern (useActionState) — consistent with current docs
B) Match existing code (useState) — consistent with codebase
→ Which approach do you prefer?
```

Surface the conflict. Don't silently pick one.

### Step 4: Cite Your Sources

Every framework-specific pattern gets a citation. The user must be able to verify every decision.

**In code comments:**

```typescript
// React 19 form handling with useActionState
// Source: https://react.dev/reference/react/useActionState#usage
const [state, formAction, isPending] = useActionState(submitOrder, initialState);
```

**In conversation:**

```
I'm using useActionState instead of manual useState for the
form submission state. React 19 replaced the manual
isPending/setIsPending pattern with this hook.

Source: https://react.dev/blog/2024/12/05/react-19#actions
"useTransition now supports async functions [...] to handle
pending states automatically"
```

**Citation rules:**

- Full URLs, not shortened
- Prefer deep links with anchors where possible (e.g. `/useActionState#usage` over `/useActionState`) — anchors survive doc restructuring better than top-level pages
- Quote the relevant passage when it supports a non-obvious decision
- Include browser/runtime support data when recommending platform features
- If you cannot find documentation for a pattern, say so explicitly:

```
UNVERIFIED: I could not find official documentation for this
pattern. This is based on training data and may be outdated.
Verify before using in production.
```

Honesty about what you couldn't verify is more valuable than false confidence.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I already know this project" | You don't. Specs change, plans evolve, decisions get made in other sessions. Training data is a snapshot — `.ai-runtime-artifacts/` is the living record. Read it. |
| "Reading project docs wastes tokens" | Re-implementing the wrong design and having the user correct you wastes far more. One `Read` of a spec prevents hours of rework across sessions. |
| "The user will tell me if I'm wrong" | Making the user repeat design decisions they already documented is disrespectful of their time. Read the docs — they exist precisely so you don't need to be re-trained. |
| "I'm confident about this API" | Confidence is not evidence. Training data contains outdated patterns that look correct but break against current versions. Verify. |
| "Fetching docs wastes tokens" | Hallucinating an API wastes more. The user debugs for an hour, then discovers the function signature changed. One fetch prevents hours of rework. |
| "The docs won't have what I need" | If the docs don't cover it, that's valuable information — the pattern may not be officially recommended. |
| "I'll just mention it might be outdated" | A disclaimer doesn't help. Either verify and cite, or clearly flag it as unverified. Hedging is the worst option. |
| "This is a simple task, no need to check" | Simple tasks with wrong patterns become templates. The user copies your deprecated form handler into ten components before discovering the modern approach exists. |

## Red Flags

- **Jumping straight to coding without checking `.ai-runtime-artifacts/`** — this is the #1 cause of "retraining from scratch" across sessions
- **Assuming you "remember" the spec/plan from a past conversation** — you don't; read the actual files
- **Not checking for conflicting artifacts** — two specs saying different things means a decision was made elsewhere; surface it
- Writing framework-specific code without checking the docs for that version
- Using "I believe" or "I think" about an API instead of citing the source
- Implementing a pattern without knowing which version it applies to
- Citing Stack Overflow or blog posts instead of official documentation
- Using deprecated APIs because they appear in training data
- Not reading `package.json` / dependency files before implementing
- Delivering code without source citations for framework-specific decisions
- Fetching an entire docs site when only one page is relevant

## Verification

After implementing with source-driven development:

- [ ] **Step 0 executed**: `.ai-runtime-artifacts/` scanned for related specs/plans/decisions; results stated to user
- [ ] **Project context loaded**: `project.profile.md` + `context-map.md` read (unless Tier 0 mechanical fix)
- [ ] **Existing artifacts reconciled**: no conflicts between existing docs surfaced silently; conflicts raised to user
- 产物已写入 `.ai-runtime-artifacts/stack/YYYY-MM-DD-stack.md`（FM: `route: source-driven-development`, `skills: source-driven-development`, Stack Detection 结果）
- Framework and library versions were identified from the dependency file
- Official documentation was fetched for framework-specific patterns
- All sources are official documentation, not blog posts or training data
- Code follows the patterns shown in the current version's documentation
- Non-trivial decisions include source citations with full URLs
- No deprecated APIs are used (checked against migration guides)
- Conflicts between docs and existing code were surfaced to the user
- Anything that could not be verified is explicitly flagged as unverified
