const fs = require('fs');
const path = require('path');
const { error, printJson, ensurePlanningDir, readText, writeText } = require('./core.cjs');
const { extractFrontmatter } = require('./frontmatter.cjs');

function statePath(cwd) {
  return path.join(ensurePlanningDir(cwd), 'STATE.md');
}

function loadStateFrontmatter(cwd) {
  const p = statePath(cwd);
  if (!fs.existsSync(p)) return {};
  const { data } = extractFrontmatter(readText(p));
  return data || {};
}

function cmdStateLoad(cwd, raw) {
  const p = statePath(cwd);
  if (!fs.existsSync(p)) error(`Missing STATE.md at ${p}`);
  printJson({ ok: true, path: p }, raw);
}

function cmdStateJson(cwd, raw) {
  printJson(loadStateFrontmatter(cwd), raw);
}

function cmdStateGet(cwd, section, raw) {
  const p = statePath(cwd);
  if (!fs.existsSync(p)) error(`Missing STATE.md at ${p}`);
  const text = readText(p);
  if (!section) {
    printJson({ content: text }, raw);
    return;
  }
  // Simple section extractor by heading "## {section}"
  const re = new RegExp(`^##\\s+${String(section).replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')}\\s*$([\\s\\S]*?)(^##\\s+|\\Z)`, 'm');
  const m = text.match(re);
  printJson({ section, found: Boolean(m), content: m ? m[1].trim() : null }, raw);
}

function cmdStateUpdate(cwd, field, value) {
  error('state update not implemented in this workspace');
}
function cmdStatePatch() { error('state patch not implemented in this workspace'); }
function cmdStateAdvancePlan() { error('state advance-plan not implemented in this workspace'); }
function cmdStateRecordMetric() { error('state record-metric not implemented in this workspace'); }
function cmdStateUpdateProgress() { error('state update-progress not implemented in this workspace'); }
function cmdStateAddDecision() { error('state add-decision not implemented in this workspace'); }
function cmdStateAddBlocker() { error('state add-blocker not implemented in this workspace'); }
function cmdStateResolveBlocker() { error('state resolve-blocker not implemented in this workspace'); }
function cmdStateRecordSession() { error('state record-session not implemented in this workspace'); }
function cmdStateSnapshot(cwd, raw) {
  const p = statePath(cwd);
  printJson({ path: p, frontmatter: loadStateFrontmatter(cwd) }, raw);
}

module.exports = {
  cmdStateLoad,
  cmdStateJson,
  cmdStateGet,
  cmdStateUpdate,
  cmdStatePatch,
  cmdStateAdvancePlan,
  cmdStateRecordMetric,
  cmdStateUpdateProgress,
  cmdStateAddDecision,
  cmdStateAddBlocker,
  cmdStateResolveBlocker,
  cmdStateRecordSession,
  cmdStateSnapshot,
};

