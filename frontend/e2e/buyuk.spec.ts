import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, test } from "@playwright/test";

const texts = JSON.parse(readFileSync("src/texts.json", "utf8"));
const N = 10_000;

/** 10 real golden records (public/ornek_toplu.csv) repeated 1000 times with distinct kayit_id. */
function buyukCsv(): string {
  const [head, ...rows] = readFileSync("public/ornek_toplu.csv", "utf8").trim().split("\n");
  const out = [head];
  for (let i = 0; i < N; i++) {
    const r = rows[i % rows.length];
    out.push(`${r.slice(0, r.lastIndexOf(","))},b${i}`);
  }
  return `${out.join("\n")}\n`;
}

test("10.000 satırlık CSV arayüzden yüklenir: süre ve özet", async ({ page }) => {
  test.setTimeout(180_000);
  const dir = mkdtempSync(join(tmpdir(), "cc-"));
  const dosya = join(dir, "buyuk.csv");
  writeFileSync(dosya, buyukCsv());

  await page.goto("/");
  await page.locator('[data-sekme="toplu"]').click();
  await page.setInputFiles("#csv-dosya", dosya);

  const t0 = Date.now();
  await page.getByRole("button", { name: texts.toplu.yukle }).click();
  await expect(page.locator('[data-ozet="n"]')).toHaveText("10.000", { timeout: 120_000 });
  const sure = Date.now() - t0;

  const ozet = {
    n: await page.locator('[data-ozet="n"]').innerText(),
    destek_disi: await page.locator('[data-ozet="destek_disi"]').innerText(),
    plan_arayan: await page.locator('[data-ozet="plan_arayan"]').innerText(),
    gecerli_plan_orani: await page.locator('[data-ozet="gecerli_plan_orani"]').innerText(),
    gosterilen_satir: await page.locator('[data-toplu="satirlar"] tbody tr').count(),
  };
  console.log(`BUYUK_CSV sure_ms=${sure} ${JSON.stringify(ozet)}`);
  await expect(page.locator("[data-uyari-seridi]")).toBeVisible();
  expect(sure).toBeLessThan(60_000);

  const [indirme] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: texts.toplu.sonuc_indir }).click(),
  ]);
  const satirlar = readFileSync(await indirme.path(), "utf8").trim().split("\n");
  expect(satirlar).toHaveLength(N + 1);
  if (process.env.SCREENSHOTS) await page.screenshot({ path: "../docs/ui/toplu-10000.png" });
});
