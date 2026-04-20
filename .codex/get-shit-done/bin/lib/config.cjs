const path = require('path');
const { ensurePlanningDir, error, readJson, writeJson, printJson, parseScalar, getDeep, setDeep } = require('./core.cjs');

function configPath(cwd) {
  const planningDir = ensurePlanningDir(cwd);
  return path.join(planningDir, 'config.json');
}

function loadConfig(cwd) {
  const p = configPath(cwd);
  return readJson(p, {});
}

function saveConfig(cwd, cfg) {
  const p = configPath(cwd);
  writeJson(p, cfg, { pretty: true });
}

function cmdConfigEnsureSection(cwd, raw) {
  const cfg = loadConfig(cwd);
  if (!cfg.workflow || typeof cfg.workflow !== 'object') cfg.workflow = {};
  saveConfig(cwd, cfg);
  printJson({ ok: true, path: '.planning/config.json' }, raw);
}

function cmdConfigSet(cwd, dottedKey, value, raw) {
  if (!dottedKey) error('config-set requires a key like workflow.auto_advance');
  const cfg = loadConfig(cwd);
  setDeep(cfg, dottedKey, parseScalar(value));
  saveConfig(cwd, cfg);
  printJson({ ok: true, key: dottedKey, value: getDeep(cfg, dottedKey) }, raw);
}

function cmdConfigGet(cwd, dottedKey, raw) {
  if (!dottedKey) error('config-get requires a key like workflow.auto_advance');
  const cfg = loadConfig(cwd);
  const value = getDeep(cfg, dottedKey);
  printJson(value === undefined ? null : value, raw);
}

module.exports = {
  cmdConfigEnsureSection,
  cmdConfigSet,
  cmdConfigGet,
  loadConfig,
  configPath,
};

