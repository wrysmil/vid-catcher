#!/usr/bin/env node
/**
 * scan-artifacts-graph.js
 * ─────────────────────────────────────────────────────────────
 * 扫描 `.ai-runtime-artifacts/` 下的产物 front matter，
 * 用现有字段（dispatch / plan / source / topic / batch_id / route / artifact）
 * 推导出「产物之间」的知识关系，输出 `graph.json`。
 *
 * 设计原则（对齐 README § 只读产物）：
 *   1. 只读：不修改任何产物文件。
 *   2. 无侵入：不强迫 AI 新增标记，优先用已有字段推导关系。
 *   3. 真实 + 演示：扫描真实产物；另附一个 mock 批次（auth-batch）用于演示
 *      当产物尚未落盘时的完整批次链路（spec→plan→dispatch→test→review）。
 *
 * 用法：
 *   node scan-artifacts-graph.js [artifacts-dir] [--out graph.json]
 *   默认：.ai-runtime-artifacts/  →  stdout 或 --out 指定文件
 *
 * 依赖：无（纯 Node 内置 fs/path）。
 */

const fs = require('fs');
const path = require('path');

// ─── 可配置项 ─────────────────────────────────────────────
// ─── 可配置项 ─────────────────────────────────────────────
// 用法: node scan-artifacts-graph.js [artifacts-dir] [--out graph.json]
let ARTIFACT_ROOT = '.ai-runtime-artifacts';
let OUT = null;
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--out') {
    OUT = path.resolve(argv[i + 1]);
    i++;
  } else if (!argv[i].startsWith('--')) {
    ARTIFACT_ROOT = argv[i];
  }
}

// ─── 产物「类别」→ 图谱节点 type 映射 ─────────────────────
// 用于给节点着色 / 归组。依据 core/artifacts.md 的 Artifact 类型。
const TYPE_BY_ARTIFACT = {
  'spec': 'spec',
  'implementation-plan': 'plan',
  'implementation-dispatch': 'dispatch',
  'review': 'review',
  'document-review': 'review',
  'verification': 'verification',
  'verification-lite': 'verification',
  'execution-log': 'log',
  'dispatch-track': 'track',
  'handoff': 'log',
  'wu-checklist': 'log',
  'decision-record': 'decision',
  'retro': 'retro',
  'research-report': 'research',
  'project-profile': 'profile',
  'context-map': 'profile',
};

// 从 `source:` 字段里抓出「上游产物/文档」的路径。
// 产物间靠这些路径连边（spec→plan→review 之类）。
const SOURCE_ARTIFACT_RE = [
  /(specs|plans|verifications|reviews|decisions|research|execution-logs)\/.*\.md/i,
  /docs\/superpowers\/specs\/.*\.md/i,
];

// ─── Front matter 解析（超轻量）───────────────────────────
function parseFrontMatter(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---\n/);
  if (!m) return {};
  const fm = {};
  let cur = null; // 当前顶层 key
  m[1].split('\n').forEach((line) => {
    const top = line.match(/^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$/);
    if (top) {
      cur = top[1];
      const v = top[2].trim();
      if (v === '' ) {
        // 空值后可能跟列表；先初始化为数组，后续 '-' 项 push
        fm[cur] = [];
        // 保持 cur 有效，用于收集列表项
      } else if (v.startsWith('[') && v.endsWith(']')) {
        fm[cur] = v.slice(1, -1).split(',').map((s) => s.trim()).filter(Boolean);
        cur = null;
      } else {
        // 简单标量值（日期、字符串等）
        fm[cur] = v.replace(/^["']|["']$/g, '');
        cur = null;
      }
    } else if (cur && /^\s+- /.test(line)) {
      const val = line.trim().replace(/^-\s+/, '').replace(/^["']|["']$/g, '');
      if (Array.isArray(fm[cur])) fm[cur].push(val);
      else fm[cur] = [val];
    }
  });
  // 若字段在空值后没收到任何列表项，转为空字符串（避免残留空数组）
  Object.keys(fm).forEach((k) => {
    if (Array.isArray(fm[k]) && fm[k].length === 0) fm[k] = '';
  });
  return fm;
}

// ─── 文件路径 → 相对产物标识 ──────────────────────────────
function relPath(fileAbs, root) {
  let rel = path.relative(root, fileAbs);
  if (rel === '' || rel.startsWith('..')) rel = fileAbs;
  return rel.split(path.sep).join('/');
}

function stemOf(rel) {
  return path.basename(rel, '.md');
}

// 从文件名推断 topic / date（YYYY-MM-DD-<topic>-<artifact>）
function metaFromFilename(rel) {
  const base = path.basename(rel, '.md');
  const m = base.match(/^(\d{4}-\d{2}-\d{2})-?(.*)$/);
  const b = base.replace(/^\d{4}-\d{2}-\d{2}-?/, '');
  return {
    date: m ? m[1] : '',
    topic: b,
  };
}

// ─── 主扫描 ─────────────────────────────────────────────
function scan(root) {
  const files = [];
  (function walk(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    entries.forEach((e) => {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith('.md')) files.push(p);
    });
  })(root);

  const nodes = [];
  const edges = [];
  const seenIds = new Set();

  const nodeMap = {};
  function ensureNode(id, label, type, extra = {}) {
    if (!nodeMap[id]) {
      nodeMap[id] = { id, label, type, ...extra };
      nodes.push(nodeMap[id]);
    }
    return nodeMap[id];
  }
  function addEdge(from, to, label, opts = {}) {
    if (from === to) return;
    const key = `${from}|${label}|${to}`;
    if (seenIds.has(key)) return;
    seenIds.add(key);
    edges.push({ from, to, label, ...opts });
  }

  const find = (rel) => nodeMap[rel];

  files.forEach((fileAbs) => {
    const rel = relPath(fileAbs, root);
    const text = fs.readFileSync(fileAbs, 'utf8');
    const fm = parseFrontMatter(text);
    const artifact = fm.artifact || 'artifact';
    const type = TYPE_BY_ARTIFACT[artifact] || 'artifact';
    const topic = fm.topic || metaFromFilename(rel).topic || '';

    // 当前产物节点
    const self = ensureNode(rel, `${path.basename(rel, '.md')}`, type, {
      artifact,
      route: fm.route || '',
      date: fm.created_at || metaFromFilename(rel).date || '',
      topic,
      verdict: fm.verdict || fm.reviewed_doc_status || '',
    });

    // 1) dispatch 指针 → plan→dispatch 边
    if (fm.dispatch && fm.dispatch !== 'n/a' && fm.dispatch !== 'none') {
      const dep = fm.dispatch.split(',').map((s) => s.trim()).filter(Boolean);
      dep.forEach((d) => {
        const dRel = d.startsWith('..') || d.startsWith('/') ? d : path.posix.join(root, d);
        addEdge(rel, d, 'dispatches→');
        // 反向也建（如果被指向文件存在）
      });
    }
    // dispatch 产物里的 plan → 反向
    if (fm.plan) {
      addEdge(rel, fm.plan, 'plan→');
    }

    // 2) source 里提取上游产物/文档
    if (Array.isArray(fm.source)) {
      fm.source.forEach((s) => {
        SOURCE_ARTIFACT_RE.forEach((re) => {
          const mm = String(s).match(re);
          if (mm) {
            const target = String(s).replace(/^harness-kit\//, '');
            // 是 .ai-runtime-artifacts 内产物 → 连边；否则作为来源文档节点
            if (/^(specs|plans|verifications|reviews|decisions|research|execution-logs)\//.test(target)) {
              const targetId = path.posix.join(root, target);
              addEdge(rel, targetId, 'sources→');
            } else {
              const srcNode = ensureNode('src:' + target, target.split('/').pop().replace('.md', ''), 'source-doc', {
                path: target,
              });
              addEdge(rel, srcNode.id, 'from→');
            }
          }
        });
      });
    }

    // 3) topic / batch_id → 聚类边
    if (topic) self.topic = topic;
    if (fm.batch_id) self.batch = fm.batch_id;

    // 4) route → 承载节点（route 里含 skill 链）
    if (fm.route) {
      const routes = fm.route.split(/->|→/).map((s) => s.trim()).filter(Boolean);
      routes.forEach((r) => {
        // 只保留形如 xxx:yyy 或 xxx 的 skill/阶段标识，作为 skill 节点
        if (/^[A-Za-z0-9_.-]+(:[A-Za-z0-9_.-]+)?$/.test(r) && !r.startsWith('.')) {
          // 归一化：去掉 superpowers: / cursor-orchestration: 前缀，避免同 skill 重复
          const norm = r.split(':').pop();
          const skillId = ensureNode('skill:' + norm, norm, 'skill', {});
          addEdge(rel, skillId.id, 'uses→');
        }
      });
    }
    // skills 列表 → 节点 + 边
    if (Array.isArray(fm.skills)) {
      fm.skills.filter((sk) => typeof sk === 'string' && sk.trim() && !/^[\{\[]/.test(sk)).forEach((sk) => {
        const skNode = ensureNode('skill:' + sk, sk, 'skill', {});
        addEdge(rel, skNode.id, 'uses→');
      });
    }
  });

  // topic / batch 聚类：把同 topic 产物连成一批
  const byTopic = {};
  nodes.forEach((n) => {
    if (n.topic) {
      byTopic[n.topic] = byTopic[n.topic] || [];
      byTopic[n.topic].push(n.id);
      // 全部指向一个 batch 汇聚节点，或用环。这里用「同一主题」连一条弱边
    }
  });
  Object.keys(byTopic).forEach((t) => {
    const ids = byTopic[t];
    if (ids.length > 1) {
      for (let i = 0; i < ids.length; i++) {
        for (let j = i + 1; j < ids.length; j++) {
          addEdge(ids[i], ids[j], 'topic', { kind: 'cluster', dashed: true });
        }
      }
    }
  });

  // 补齐被引用但未扫描到的节点（以文件形式标注为未知/外部）
  const extPrefixes = ['..', '/', 'src:', 'skill:'];
  edges.forEach((e) => {
    [e.from, e.to].forEach((id) => {
      if (!nodeMap[id]) {
        // 不在扫描集内 → 建一个外部产物占位节点
        const label = id.split('/').pop().replace('.md', '');
        ensureNode(id, label, 'unresolved', { unresolved: true });
      }
    });
  });

  return { nodes, edges };
}

// ─── Demo 数据：auth-batch 完整批次链路（未落盘占位）────────
// 用于演示「当产物齐全时」的完整图谱。只用于演示，标记 demo:true。
function demoBatch() {
  const nodes = [];
  const edges = [];
  const nodeMap = {};
  function n(id, label, type, extra = {}) {
    const nd = { id, label, type, demo: true, ...extra };
    nodeMap[id] = nd;
    nodes.push(nd);
  }
  function e(from, to, label, opts = {}) {
    if (!nodeMap[from] || !nodeMap[to]) return;
    edges.push({ from, to, label, demo: true, ...opts });
  }
  const R = '.ai-runtime-artifacts/';
  n(R + 'specs/2026-05-14-auth-batch-spec.md', 'auth-batch-spec', 'spec', { topic: 'auth-batch', date: '2026-05-14' });
  n(R + 'plans/2026-05-28-auth-batch-plan.md', 'auth-batch-plan', 'plan', { topic: 'auth-batch', date: '2026-05-28' });
  n(R + 'plans/2026-05-28-auth-batch-dispatch.md', 'auth-batch-dispatch', 'dispatch', { topic: 'auth-batch', date: '2026-05-28' });
  n(R + 'execution-logs/tracking/2026-05-28-auth-batch-track.md', 'auth-batch-track', 'track', { topic: 'auth-batch', date: '2026-05-28' });
  n(R + 'verifications/2026-05-28-auth-batch-collective-test.md', 'auth-batch-collective-test', 'verification', { topic: 'auth-batch', date: '2026-05-28', verdict: 'PASS' });
  n(R + 'reviews/2026-05-28-auth-batch-code-review.md', 'auth-batch-code-review', 'review', { topic: 'auth-batch', date: '2026-05-28', verdict: 'APPROVE' });
  n('skill:brainstorming', 'brainstorming', 'skill');
  n('skill:writing-plans', 'writing-plans', 'skill');
  n('skill:verification-before-completion', 'verification-before-completion', 'skill');
  n('skill:requesting-code-review', 'requesting-code-review', 'skill');
  n('skill:orchestration', 'orchestration', 'skill');
  n('src:docs/superpowers/specs/2026-05-14-auth-batch-design.md', 'auth-batch-design', 'source-doc');

  e(R + 'specs/2026-05-14-auth-batch-spec.md', 'src:docs/superpowers/specs/2026-05-14-auth-batch-design.md', 'from→');
  e(R + 'specs/2026-05-14-auth-batch-spec.md', 'skill:brainstorming', 'uses→');
  e(R + 'plans/2026-05-28-auth-batch-plan.md', R + 'specs/2026-05-14-auth-batch-spec.md', 'dispatches→');
  e(R + 'plans/2026-05-28-auth-batch-plan.md', 'skill:writing-plans', 'uses→');
  e(R + 'plans/2026-05-28-auth-batch-dispatch.md', R + 'plans/2026-05-28-auth-batch-plan.md', 'plan→');
  e(R + 'plans/2026-05-28-auth-batch-dispatch.md', 'skill:orchestration', 'uses→');
  e(R + 'execution-logs/tracking/2026-05-28-auth-batch-track.md', R + 'plans/2026-05-28-auth-batch-dispatch.md', 'tracks→');
  e(R + 'verifications/2026-05-28-auth-batch-collective-test.md', 'skill:verification-before-completion', 'uses→');
  e(R + 'reviews/2026-05-28-auth-batch-code-review.md', 'skill:requesting-code-review', 'uses→');
  e(R + 'reviews/2026-05-28-auth-batch-code-review.md', R + 'verifications/2026-05-28-auth-batch-collective-test.md', 'after→');
  return { nodes, edges };
}

function main() {
  if (!fs.existsSync(ARTIFACT_ROOT)) {
    console.error(`[ERR] 产物目录不存在: ${ARTIFACT_ROOT}`);
    process.exit(1);
  }
  const real = scan(ARTIFACT_ROOT);
  const demo = demoBatch();
  const graph = {
    meta: {
      generated_at: new Date().toISOString(),
      real_count: real.nodes.length,
      demo_count: demo.nodes.length,
      root: ARTIFACT_ROOT,
      note: 'real=扫描产物；demo=auth-batch 占位示例（未落盘）。蓝色实线=推导关系，虚线=topic 聚类。',
    },
    nodes: [...real.nodes, ...demo.nodes],
    edges: [...real.edges, ...demo.edges],
  };

  const out = JSON.stringify(graph, null, 2);
  if (OUT) {
    fs.writeFileSync(OUT, out);
    console.log(`✅ 已写入 ${OUT}`);
    console.log(`   real 节点 ${real.nodes.length} / 边 ${real.edges.length}；demo 节点 ${demo.nodes.length} / 边 ${demo.edges.length}`);
  } else {
    console.log(out);
  }
}

main();
