import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const sourceDir = path.resolve(rootDir, "..", "credit-coach", "artifacts", "runs");
const targetDir = path.resolve(rootDir, "demo-data");

async function main() {
  const runs = await fs.readdir(sourceDir).catch(() => []);
  if (!runs.length) {
    console.log("No artifact runs found. Keeping existing curated demo data.");
    return;
  }

  console.log(
    [
      "This script is a placeholder for later artifact sync automation.",
      `Detected ${runs.length} run directories under ${sourceDir}.`,
      `Curated website snapshots remain under ${targetDir}.`,
    ].join(" "),
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
