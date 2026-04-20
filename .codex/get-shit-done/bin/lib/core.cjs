const fs = require('fs');
const path = require('path');

function error(message, exitCode = 1) {
  // Keep behavior simple and deterministic for workflow scripts.
  console.error(String(message || 'Unknown error'));
  process.exit(exitCode);
}

function readText(filePath) {
  return fs.readFileSync(filePath, 'utf8');
}

function writeText(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, 'utf8');
}

function safeJsonParse(text, fallback = null) {
  try {
    return JSON.parse(text);
  } catch {
    return fallback;
  }
}

function readJson(filePath, fallback = null) {
  if (!fs.existsSync(filePath)) return fallback;
  const text = readText(filePath);
  return safeJsonParse(text, fallback);
}

function writeJson(filePath, obj, { pretty = true } = {}) {
  const content = pretty ? `${JSON.stringify(obj, null, 2)}\n` : JSON.stringify(obj);
  writeText(filePath, content);
}

function printJson(obj, raw) {
  if (raw) {
    process.stdout.write(JSON.stringify(obj));
    process.stdout.write('\n');
  } else {
    process.stdout.write(JSON.stringify(obj, null, 2));
    process.stdout.write('\n');
  }
}

function parseScalar(value) {
  const trimmed = String(value ?? '').trim();
  if (trimmed === '') return '';
  if (trimmed === 'null') return null;
  if (trimmed === 'true') return true;
  if (trimmed === 'false') return false;
  if (trimmed === '[]') return [];
  if (trimmed === '{}') return {};
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed);

  // Strip surrounding single/double quotes if present.
  const m = trimmed.match(/^["'](.*)["']$/);
  return m ? m[1] : trimmed;
}

function getDeep(obj, dottedPath) {
  const keys = String(dottedPath || '').split('.').filter(Boolean);
  let current = obj;
  for (const key of keys) {
    if (!current || typeof current !== 'object' || !(key in current)) return undefined;
    current = current[key];
  }
  return current;
}

function setDeep(obj, dottedPath, value) {
  const keys = String(dottedPath || '').split('.').filter(Boolean);
  if (keys.length === 0) return obj;
  let current = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    if (!current[key] || typeof current[key] !== 'object') current[key] = {};
    current = current[key];
  }
  current[keys[keys.length - 1]] = value;
  return obj;
}

function ensurePlanningDir(cwd) {
  const planningDir = path.join(cwd, '.planning');
  if (!fs.existsSync(planningDir)) {
    error(`Missing .planning/ directory at: ${planningDir}`);
  }
  return planningDir;
}

module.exports = {
  error,
  readText,
  writeText,
  safeJsonParse,
  readJson,
  writeJson,
  printJson,
  parseScalar,
  getDeep,
  setDeep,
  ensurePlanningDir,
};

