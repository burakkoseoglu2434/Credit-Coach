const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { error, printJson, ensurePlanningDir } = require('./core.cjs');
const config = require('./config.cjs');

function runGit(cwd, args) {
  const res = spawnSync('git', args, { cwd, stdio: 'pipe', encoding: 'utf8' });
  if (res.status !== 0) {
    error(`git ${args.join(' ')} failed:\n${res.stderr || res.stdout}`);
  }
  return res.stdout.trim();
}

function cmdResolveModel(cwd, agentType, raw) {
  const cfg = config.loadConfig(cwd);
  const profile = cfg.model_profile || 'balanced';
  // Codex CLI chooses models per role; keep this for workflow JSON compatibility only.
  const mapping = {
    balanced: { executor: 'inherit', verifier: 'inherit' },
    quality: { executor: 'inherit', verifier: 'inherit' },
    budget: { executor: 'inherit', verifier: 'inherit' },
  };
  const out = { agent_type: agentType || null, profile, model: mapping[profile]?.executor || 'inherit' };
  printJson(out, raw);
}

function cmdCommit(cwd, message, files, raw, amend = false) {
  if (!message) error('commit requires a message');
  if (!files || files.length === 0) error('commit requires --files with at least one path');

  for (const f of files) {
    runGit(cwd, ['add', '--', f]);
  }

  const args = ['commit', '-m', message];
  if (amend) args.push('--amend', '--no-edit');
  runGit(cwd, args);
  const hash = runGit(cwd, ['rev-parse', '--short', 'HEAD']);
  printJson({ ok: true, hash, message, files }, raw);
}

function cmdGenerateSlug(text, raw) {
  const slug = String(text || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  printJson({ slug }, raw);
}

function cmdCurrentTimestamp(format, raw) {
  const now = new Date();
  const iso = now.toISOString();
  const date = iso.slice(0, 10);
  const filename = iso.replace(/[:.]/g, '').replace('T', '_').slice(0, 15) + 'Z';
  const out = format === 'date' ? date : (format === 'filename' ? filename : iso);
  printJson({ timestamp: out }, raw);
}

function cmdVerifyPathExists(cwd, target, raw) {
  const p = path.resolve(cwd, target);
  printJson({ path: target, exists: fs.existsSync(p) }, raw);
}

function cmdListTodos(cwd, area, raw) {
  // Minimal placeholder: enumerate .planning/todos if exists.
  const planningDir = ensurePlanningDir(cwd);
  const todosDir = path.join(planningDir, 'todos');
  if (!fs.existsSync(todosDir)) {
    printJson({ ok: true, area: area || null, count: 0, items: [] }, raw);
    return;
  }
  const items = fs.readdirSync(todosDir).filter(f => f.endsWith('.md')).sort();
  printJson({ ok: true, area: area || null, count: items.length, items }, raw);
}

function cmdHistoryDigest() {
  error('history-digest not implemented in this workspace');
}
function cmdProgressRender() {
  error('progress not implemented in this workspace');
}
function cmdTodoComplete() {
  error('todo complete not implemented in this workspace');
}
function cmdSummaryExtract() {
  error('summary-extract not implemented in this workspace');
}
async function cmdWebsearch() {
  error('websearch not implemented in this workspace');
}
function cmdScaffold() {
  error('scaffold not implemented in this workspace');
}

module.exports = {
  cmdResolveModel,
  cmdCommit,
  cmdGenerateSlug,
  cmdCurrentTimestamp,
  cmdListTodos,
  cmdVerifyPathExists,
  cmdHistoryDigest,
  cmdProgressRender,
  cmdTodoComplete,
  cmdSummaryExtract,
  cmdWebsearch,
  cmdScaffold,
};

