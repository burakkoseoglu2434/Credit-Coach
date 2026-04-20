const fs = require('fs');
const path = require('path');
const { error, printJson, ensurePlanningDir } = require('./core.cjs');
const { extractFrontmatter } = require('./frontmatter.cjs');

function phaseRoot(cwd) {
  const planningDir = ensurePlanningDir(cwd);
  return path.join(planningDir, 'phases');
}

function listPhaseDirs(cwd, { includeArchived = false } = {}) {
  const dirs = [];
  const root = phaseRoot(cwd);
  if (fs.existsSync(root)) {
    for (const ent of fs.readdirSync(root, { withFileTypes: true })) {
      if (ent.isDirectory()) dirs.push(path.join(root, ent.name));
    }
  }
  if (includeArchived) {
    const milestonesDir = path.join(ensurePlanningDir(cwd), 'milestones');
    if (fs.existsSync(milestonesDir)) {
      for (const ent of fs.readdirSync(milestonesDir, { withFileTypes: true })) {
        if (!ent.isDirectory()) continue;
        const maybePhasesDir = path.join(milestonesDir, ent.name, 'phases');
        if (!fs.existsSync(maybePhasesDir)) continue;
        for (const p of fs.readdirSync(maybePhasesDir, { withFileTypes: true })) {
          if (p.isDirectory()) dirs.push(path.join(maybePhasesDir, p.name));
        }
      }
    }
  }
  return dirs;
}

function findPhaseDir(cwd, phaseArg, { includeArchived = false } = {}) {
  const phaseNumber = String(phaseArg ?? '').trim();
  if (!phaseNumber) return null;

  const dirs = listPhaseDirs(cwd, { includeArchived });
  const matches = dirs
    .map(d => ({ dir: d, name: path.basename(d) }))
    .filter(x => x.name.startsWith(`${phaseNumber}-`));

  if (matches.length === 0) return null;
  // Prefer shortest name match (guards against "72-foo" and "72.1-foo")
  matches.sort((a, b) => a.name.length - b.name.length);
  return matches[0].dir;
}

function listPlanFiles(phaseDir) {
  const entries = fs.readdirSync(phaseDir, { withFileTypes: true });
  return entries
    .filter(e => e.isFile() && e.name.endsWith('-PLAN.md'))
    .map(e => path.join(phaseDir, e.name))
    .sort((a, b) => a.localeCompare(b));
}

function planIdFromFilename(filename) {
  // Example: 72-01-PLAN.md -> 72-01
  return filename.replace(/-PLAN\.md$/, '');
}

function objectiveFromText(text) {
  const m = text.match(/<objective>\s*([\s\S]*?)\s*<\/objective>/i);
  if (!m) return null;
  return m[1].trim().replace(/\s+/g, ' ');
}

function readPlanIndexEntry(planPath) {
  const text = fs.readFileSync(planPath, 'utf8');
  const { data } = extractFrontmatter(text);
  const filename = path.basename(planPath);
  const id = planIdFromFilename(filename);
  const summaryPath = planPath.replace(/-PLAN\.md$/, '-SUMMARY.md');

  const wave = Number.isFinite(Number(data.wave)) ? Number(data.wave) : 1;
  const autonomous = typeof data.autonomous === 'boolean' ? data.autonomous : true;
  const filesModified = Array.isArray(data.files_modified) ? data.files_modified : [];
  const taskCount = (text.match(/<task\b/g) || []).length;
  const hasCheckpoints = /type="checkpoint/i.test(text);
  const objective = objectiveFromText(text);

  return {
    id,
    wave,
    autonomous,
    objective,
    files_modified: filesModified,
    task_count: taskCount,
    has_summary: fs.existsSync(summaryPath),
    has_checkpoints: hasCheckpoints,
    plan_file: filename,
    summary_file: path.basename(summaryPath),
  };
}

function cmdFindPhase(cwd, phaseArg, raw) {
  const dir = findPhaseDir(cwd, phaseArg, { includeArchived: true });
  printJson({ phase: String(phaseArg ?? ''), found: Boolean(dir), dir }, raw);
}

function cmdPhasePlanIndex(cwd, phaseArg, raw) {
  const dir = findPhaseDir(cwd, phaseArg);
  if (!dir) error(`Phase not found: ${phaseArg}`);

  const plans = listPlanFiles(dir).map(readPlanIndexEntry);
  const waves = {};
  const incomplete = [];
  let hasCheckpoints = false;

  for (const p of plans) {
    if (!waves[p.wave]) waves[p.wave] = [];
    waves[p.wave].push(p.id);
    if (!p.has_summary) incomplete.push(p.id);
    if (p.has_checkpoints) hasCheckpoints = true;
  }

  const out = {
    phase: {
      number: String(phaseArg),
      dir,
      slug: path.basename(dir),
    },
    plans,
    waves,
    incomplete,
    has_checkpoints: hasCheckpoints,
  };

  printJson(out, raw);
}

function cmdPhasesList(cwd, options, raw) {
  const type = options?.type || null; // summaries | plans | all
  const phaseFilter = options?.phase ? String(options.phase) : null;
  const includeArchived = Boolean(options?.includeArchived);

  const dirs = listPhaseDirs(cwd, { includeArchived });
  const items = [];

  for (const dir of dirs) {
    const base = path.basename(dir);
    const m = base.match(/^(\d+(\.\d+)?)-/);
    if (!m) continue;
    const phaseNumber = m[1];
    if (phaseFilter && phaseFilter !== phaseNumber) continue;

    for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
      if (!ent.isFile()) continue;
      if (type === 'summaries' && !ent.name.endsWith('-SUMMARY.md')) continue;
      if (type === 'plans' && !ent.name.endsWith('-PLAN.md')) continue;
      if (!type && !ent.name.match(/-(PLAN|SUMMARY)\.md$/)) continue;
      items.push(path.join(dir, ent.name));
    }
  }

  items.sort((a, b) => a.localeCompare(b));
  printJson({ items, count: items.length, type, phase: phaseFilter, includeArchived }, raw);
}

// Placeholder commands (not needed for execute-phase in this repo state)
function cmdPhaseNextDecimal(cwd, phaseArg, raw) {
  const phaseNumber = String(phaseArg ?? '').trim();
  if (!phaseNumber) error('phase next-decimal requires a phase number');
  // naive: suggest +0.1
  const next = `${phaseNumber}.1`;
  printJson({ phase: phaseNumber, next }, raw);
}
function cmdPhaseAdd() { error('phase add not implemented in this workspace'); }
function cmdPhaseInsert() { error('phase insert not implemented in this workspace'); }
function cmdPhaseRemove() { error('phase remove not implemented in this workspace'); }
function cmdPhaseComplete() { error('phase complete not implemented in this workspace'); }

module.exports = {
  findPhaseDir,
  cmdFindPhase,
  cmdPhasePlanIndex,
  cmdPhasesList,
  cmdPhaseNextDecimal,
  cmdPhaseAdd,
  cmdPhaseInsert,
  cmdPhaseRemove,
  cmdPhaseComplete,
};

