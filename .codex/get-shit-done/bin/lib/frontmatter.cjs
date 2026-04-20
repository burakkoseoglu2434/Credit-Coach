const path = require('path');
const fs = require('fs');
const { error, readText, writeText, parseScalar, printJson } = require('./core.cjs');

function extractFrontmatter(text) {
  const normalized = String(text ?? '');
  if (!normalized.startsWith('---\n') && !normalized.startsWith('---\r\n')) {
    return { data: {}, body: normalized };
  }

  const lines = normalized.split(/\r?\n/);
  if (lines[0].trim() !== '---') return { data: {}, body: normalized };

  let endIdx = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === '---') {
      endIdx = i;
      break;
    }
  }
  if (endIdx === -1) return { data: {}, body: normalized };

  const fmLines = lines.slice(1, endIdx);
  const body = lines.slice(endIdx + 1).join('\n');
  const data = parseYamlLikeFrontmatter(fmLines);
  return { data, body };
}

function parseYamlLikeFrontmatter(lines) {
  // Minimal YAML subset:
  // - key: scalar
  // - key:
  //     - item
  // Does not attempt to parse nested maps-of-maps (keeps those as raw lines).
  const obj = {};

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line || /^\s*#/.test(line)) {
      i++;
      continue;
    }

    const m = line.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
    if (!m) {
      i++;
      continue;
    }

    const key = m[1];
    const rest = m[2] ?? '';

    if (rest.trim() === '') {
      // Attempt to parse a simple list
      const arr = [];
      let j = i + 1;
      while (j < lines.length) {
        const l = lines[j];
        const li = l.match(/^\s{2,}-\s+(.*)$/);
        if (!li) break;
        arr.push(parseScalar(li[1]));
        j++;
      }
      obj[key] = arr;
      i = j;
      continue;
    }

    obj[key] = parseScalar(rest);
    i++;
  }

  return obj;
}

function serializeFrontmatter(data) {
  // Basic serializer adequate for the commands we support.
  const lines = ['---'];
  for (const [k, v] of Object.entries(data || {})) {
    if (Array.isArray(v)) {
      lines.push(`${k}:`);
      for (const item of v) {
        lines.push(`  - ${String(item)}`);
      }
    } else {
      lines.push(`${k}: ${String(v)}`);
    }
  }
  lines.push('---');
  return lines.join('\n');
}

function updateFrontmatterFile(filePath, updater) {
  const abs = path.isAbsolute(filePath) ? filePath : path.resolve(filePath);
  if (!fs.existsSync(abs)) error(`Frontmatter file not found: ${filePath}`);
  const text = readText(abs);
  const { data, body } = extractFrontmatter(text);
  const updated = updater({ ...data });
  const fm = serializeFrontmatter(updated);
  const content = `${fm}\n\n${body.replace(/^\n+/, '')}`;
  writeText(abs, content.endsWith('\n') ? content : `${content}\n`);
  return updated;
}

function cmdFrontmatterGet(cwd, file, field, raw) {
  const filePath = path.resolve(cwd, file);
  if (!fs.existsSync(filePath)) error(`File not found: ${file}`);
  const { data } = extractFrontmatter(readText(filePath));
  if (field) {
    if (!(field in data)) printJson(null, raw);
    else printJson(data[field], raw);
    return;
  }
  printJson(data, raw);
}

function cmdFrontmatterSet(cwd, file, field, value, raw) {
  if (!field) error('frontmatter set requires --field');
  const filePath = path.resolve(cwd, file);
  const parsed = parseScalar(value);
  const updated = updateFrontmatterFile(filePath, data => {
    data[field] = parsed;
    return data;
  });
  printJson({ ok: true, file, updated }, raw);
}

function cmdFrontmatterMerge(cwd, file, jsonData, raw) {
  if (!jsonData) error('frontmatter merge requires --data');
  const filePath = path.resolve(cwd, file);
  const parsed = JSON.parse(jsonData);
  const updated = updateFrontmatterFile(filePath, data => ({ ...data, ...parsed }));
  printJson({ ok: true, file, updated }, raw);
}

function cmdFrontmatterValidate(cwd, file, schema, raw) {
  // Lightweight validator to unblock workflows; strict schemas live elsewhere.
  const filePath = path.resolve(cwd, file);
  if (!fs.existsSync(filePath)) error(`File not found: ${file}`);
  const { data } = extractFrontmatter(readText(filePath));

  const requiredBySchema = {
    plan: ['phase', 'plan', 'type'],
    summary: ['phase', 'plan'],
    verification: ['phase'],
  };

  const required = requiredBySchema[schema] || [];
  const missing = required.filter(k => !(k in data));
  const ok = missing.length === 0;
  printJson({ ok, schema: schema || null, missing }, raw);
  if (!ok) process.exitCode = 2;
}

module.exports = {
  extractFrontmatter,
  parseYamlLikeFrontmatter,
  cmdFrontmatterGet,
  cmdFrontmatterSet,
  cmdFrontmatterMerge,
  cmdFrontmatterValidate,
};

