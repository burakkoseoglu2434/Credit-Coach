const fs = require('fs');
const path = require('path');
const { error, printJson, ensurePlanningDir } = require('./core.cjs');
const phase = require('./phase.cjs');

function roadmapPath(cwd) {
  return path.join(ensurePlanningDir(cwd), 'ROADMAP.md');
}

function computePlanSummaryCounts(phaseDir) {
  const entries = fs.readdirSync(phaseDir, { withFileTypes: true });
  const planCount = entries.filter(e => e.isFile() && e.name.endsWith('-PLAN.md')).length;
  const summaryCount = entries.filter(e => e.isFile() && e.name.endsWith('-SUMMARY.md')).length;
  return { planCount, summaryCount };
}

function updateProgressTableRow(lines, phaseNumber, phaseTitle, counts) {
  const { planCount, summaryCount } = counts;
  const plansComplete = `${summaryCount}/${planCount}`;
  const status = summaryCount === 0 ? 'Planned' : (summaryCount === planCount ? 'Complete' : 'In Progress');
  const completed = summaryCount === planCount ? new Date().toISOString().slice(0, 10) : '';

  const rowPrefix = `| ${phaseNumber}.`;
  const existingIdx = lines.findIndex(l => l.startsWith(rowPrefix));
  const newRow = `| ${phaseNumber}. ${phaseTitle} | v2.7 | ${plansComplete} | ${status} | ${completed} |`;

  if (existingIdx !== -1) {
    lines[existingIdx] = newRow;
    return { updated: true, inserted: false };
  }

  // Insert after the progress table header separator if present, otherwise append.
  const progressHeaderIdx = lines.findIndex(l => l.trim() === '## Progress');
  if (progressHeaderIdx === -1) {
    lines.push('');
    lines.push('## Progress');
    lines.push('');
    lines.push('| Phase | Milestone | Plans Complete | Status | Completed |');
    lines.push('|-------|-----------|----------------|--------|-----------|');
    lines.push(newRow);
    return { updated: true, inserted: true };
  }

  const tableSepIdx = lines.findIndex((l, idx) => idx > progressHeaderIdx && l.startsWith('|-------|'));
  if (tableSepIdx !== -1) {
    // Append at end of table (file currently ends with the table)
    lines.push(newRow);
    return { updated: true, inserted: true };
  }

  lines.push(newRow);
  return { updated: true, inserted: true };
}

function cmdRoadmapGetPhase(cwd, phaseNumber, raw) {
  const rp = roadmapPath(cwd);
  if (!fs.existsSync(rp)) error('Missing .planning/ROADMAP.md');
  const text = fs.readFileSync(rp, 'utf8');
  const re = new RegExp(`\\*\\*Phase ${String(phaseNumber).replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')}:([\\s\\S]*?)(\\n\\*\\*Phase |\\n## |$)`, 'm');
  const m = text.match(re);
  printJson({ phase: String(phaseNumber), found: Boolean(m), content: m ? m[0].trim() : null }, raw);
}

function cmdRoadmapAnalyze(cwd, raw) {
  // Minimal analysis: list phase numbers present on disk.
  const dirs = fs.readdirSync(path.join(ensurePlanningDir(cwd), 'phases'), { withFileTypes: true })
    .filter(e => e.isDirectory())
    .map(e => e.name)
    .sort();
  printJson({ phases_on_disk: dirs, count: dirs.length }, raw);
}

function cmdRoadmapUpdatePlanProgress(cwd, phaseNumber, raw) {
  const rp = roadmapPath(cwd);
  if (!fs.existsSync(rp)) error('Missing .planning/ROADMAP.md');
  const phaseDir = phase.findPhaseDir(cwd, phaseNumber);
  if (!phaseDir) error(`Phase not found on disk: ${phaseNumber}`);
  const phaseTitle = path.basename(phaseDir).split('-').slice(1).join(' ').replace(/\b[a-z]/g, c => c.toUpperCase());
  const counts = computePlanSummaryCounts(phaseDir);

  const lines = fs.readFileSync(rp, 'utf8').split(/\r?\n/);
  const res = updateProgressTableRow(lines, String(phaseNumber), phaseTitle, counts);
  fs.writeFileSync(rp, `${lines.join('\n')}\n`, 'utf8');

  printJson({ ok: true, phase: String(phaseNumber), ...counts, ...res }, raw);
}

module.exports = {
  cmdRoadmapGetPhase,
  cmdRoadmapAnalyze,
  cmdRoadmapUpdatePlanProgress,
};

