// Scans the BUILT UI (dist/) for forbidden phrases and the source for arithmetic helpers.
// The UI must not promise outcomes and must not compute numbers (it only formats API values).
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const phrases = JSON.parse(
  readFileSync(join(root, "..", "configs", "forbidden_phrases.json"), "utf8"),
).ifadeler;

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else yield p;
  }
}

// minifiers may escape non-ASCII characters: decode \uXXXX before matching
const decode = (s) => s.replace(/\\u([0-9a-fA-F]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));

let failures = 0;
const dist = join(root, "dist");
let scanned = 0;
for (const f of walk(dist)) {
  if (!/\.(js|html|css|csv)$/.test(f)) continue;
  scanned += 1;
  const text = decode(readFileSync(f, "utf8")).toLowerCase();
  for (const p of phrases) {
    if (text.includes(p)) {
      console.error(`forbidden phrase "${p}" in ${f}`);
      failures += 1;
    }
  }
}
if (scanned === 0) {
  console.error("nothing scanned: run `npm run build` first");
  process.exit(2);
}

// no number computing in the UI source
const banned = [/Math\./, /\.reduce\(/, /parseFloat\(/, /toFixed\(/];
for (const f of walk(join(root, "src"))) {
  if (!/\.(ts|tsx)$/.test(f) || f.endsWith("schema.d.ts")) continue;
  const text = readFileSync(f, "utf8");
  for (const re of banned) {
    if (re.test(text)) {
      console.error(`arithmetic helper ${re} in ${f}`);
      failures += 1;
    }
  }
}

if (failures > 0) process.exit(1);
console.log(`ok: ${scanned} built files scanned, ${phrases.length} phrases, no arithmetic helpers`);
