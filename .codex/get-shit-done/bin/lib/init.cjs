const fs = require('fs');
const path = require('path');
const { error, printJson, ensurePlanningDir } = require('./core.cjs');
const config = require('./config.cjs');
const phase = require('./phase.cjs');
const { extractFrontmatter } = require('./frontmatter.cjs');

function resolvePhaseNameFromDir(phaseDirName) {
  // "72-recoverability-gate-relaxation-controlled" -> "Recoverability Gate Relaxation (Controlled)"
  const parts = phaseDirName.split('-').slice(1);
  if (parts.length === 0) return phaseDirName;
  const title = parts
    .join(' ')
    .replace(/\b[a-z]/g, c => c.toUpperCase());
  return title;
}

function listPlansAndSummaries(phaseDir) {
  const entries = fs.readdirSync(phaseDir, { withFileTypes: true });
  const plans = entries.filter(e => e.isFile() && e.name.endsWith('-PLAN.md')).map(e => e.name).sort();
  const summaries = entries.filter(e => e.isFile() && e.name.endsWith('-SUMMARY.md')).map(e => e.name).sort();
  const summarySet = new Set(summaries.map(s => s.replace(/-SUMMARY\.md$/, '')));
  const incomplete = plans.filter(p => !summarySet.has(p.replace(/-PLAN\.md$/, '')));
  return { plans, summaries, incomplete };
}

function collectPhaseReqIds(phaseDir) {
  const reqIds = new Set();
  for (const planFile of fs.readdirSync(phaseDir)) {
    if (!planFile.endsWith('-PLAN.md')) continue;
    const text = fs.readFileSync(path.join(phaseDir, planFile), 'utf8');
    const { data } = extractFrontmatter(text);
    if (Array.isArray(data.requirements)) {
      for (const r of data.requirements) reqIds.add(String(r));
    }
  }
  return Array.from(reqIds).sort();
}

function cmdInitExecutePhase(cwd, phaseArg, raw) {
  ensurePlanningDir(cwd);
  const cfg = config.loadConfig(cwd);

  const phaseDir = phase.findPhaseDir(cwd, phaseArg);
  const phaseFound = Boolean(phaseDir);

  if (!phaseFound) {
    printJson({ phase_found: false, phase_arg: phaseArg }, raw);
    process.exitCode = 2;
    return;
  }

  const phaseDirName = path.basename(phaseDir);
  const phaseNumber = String(phaseArg ?? '').trim();
  const phaseName = resolvePhaseNameFromDir(phaseDirName);

  const { plans, summaries, incomplete } = listPlansAndSummaries(phaseDir);

  const out = {
    // Models are advisory in Codex CLI; keep fields for workflow compatibility.
    executor_model: 'inherit',
    verifier_model: 'inherit',
    commit_docs: cfg.commit_docs !== undefined ? Boolean(cfg.commit_docs) : true,
    parallelization: cfg.parallelization !== undefined ? Boolean(cfg.parallelization) : true,
    branching_strategy: cfg.branching_strategy || 'none',
    branch_name: cfg.branch_name || null,

    phase_found: true,
    phase_dir: phaseDir,
    phase_number: phaseNumber,
    phase_name: phaseName,
    phase_slug: phaseDirName,

    plans,
    summaries,
    incomplete_plans: incomplete,
    plan_count: plans.length,
    incomplete_count: incomplete.length,

    state_exists: fs.existsSync(path.join(cwd, '.planning', 'STATE.md')),
    roadmap_exists: fs.existsSync(path.join(cwd, '.planning', 'ROADMAP.md')),
    phase_req_ids: collectPhaseReqIds(phaseDir),

    state_path: path.join(cwd, '.planning', 'STATE.md'),
    config_path: path.join(cwd, '.planning', 'config.json'),
  };

  printJson(out, raw);
}

// Stubs for other init workflows (kept to avoid router failures)
function stub(name) {
  return function () {
    error(`init ${name} not implemented in this workspace`);
  };
}

module.exports = {
  cmdInitExecutePhase,
  cmdInitPlanPhase: stub('plan-phase'),
  cmdInitNewProject: stub('new-project'),
  cmdInitNewMilestone: stub('new-milestone'),
  cmdInitQuick: stub('quick'),
  cmdInitResume: stub('resume'),
  cmdInitVerifyWork: stub('verify-work'),
  cmdInitPhaseOp: stub('phase-op'),
  cmdInitTodos: stub('todos'),
  cmdInitMilestoneOp: stub('milestone-op'),
  cmdInitMapCodebase: stub('map-codebase'),
  cmdInitProgress: stub('progress'),
};

