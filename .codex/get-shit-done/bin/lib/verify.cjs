const fs = require('fs');
const path = require('path');
const { error, printJson } = require('./core.cjs');

function cmdVerifySummary(cwd, summaryPath, checkCount, raw) {
  const p = path.resolve(cwd, summaryPath);
  if (!fs.existsSync(p)) error(`SUMMARY not found: ${summaryPath}`);
  const text = fs.readFileSync(p, 'utf8');
  const selfCheck = /##\s+Self-Check:\s+(PASSED|FAILED)/i.exec(text);
  const ok = !selfCheck || selfCheck[1].toUpperCase() !== 'FAILED';
  printJson({ ok, summary: summaryPath, self_check: selfCheck ? selfCheck[1].toUpperCase() : null, check_count: Number(checkCount || 2) }, raw);
  if (!ok) process.exitCode = 2;
}

function cmdVerifyPlanStructure() { error('verify plan-structure not implemented in this workspace'); }
function cmdVerifyPhaseCompleteness() { error('verify phase-completeness not implemented in this workspace'); }
function cmdVerifyReferences() { error('verify references not implemented in this workspace'); }
function cmdVerifyCommits() { error('verify commits not implemented in this workspace'); }
function cmdVerifyArtifacts() { error('verify artifacts not implemented in this workspace'); }
function cmdVerifyKeyLinks() { error('verify key-links not implemented in this workspace'); }
function cmdValidateConsistency() { error('validate consistency not implemented in this workspace'); }
function cmdValidateHealth() { error('validate health not implemented in this workspace'); }

module.exports = {
  cmdVerifySummary,
  cmdVerifyPlanStructure,
  cmdVerifyPhaseCompleteness,
  cmdVerifyReferences,
  cmdVerifyCommits,
  cmdVerifyArtifacts,
  cmdVerifyKeyLinks,
  cmdValidateConsistency,
  cmdValidateHealth,
};

