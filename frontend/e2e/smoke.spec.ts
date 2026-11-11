import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const texts = JSON.parse(readFileSync("src/texts.json", "utf8"));
const SAMPLE_CSV = "public/ornek_toplu.csv";
const shots = process.env.SCREENSHOTS ? "../docs/ui" : null;

async function shot(page: Page, name: string) {
  if (shots) await page.screenshot({ path: `${shots}/${name}.png`, fullPage: true });
}

async function seritVar(page: Page) {
  const serit = page.locator("[data-uyari-seridi]");
  await expect(serit).toBeVisible();
  await expect(serit).toContainText(texts.uyari);
}

const CASES = [
  { key: "onay", tur: "onay", baslik: texts.karar.APPROVED.baslik },
  { key: "kosullu", tur: "kosullu", baslik: texts.karar.CONDITIONAL.baslik },
  { key: "ret_plan", tur: "ret_plan", baslik: texts.karar.REJECTED.baslik },
  { key: "ret_plan_yok", tur: "ret_plan_yok", baslik: texts.karar.REJECTED.baslik },
  { key: "destek_disi", tur: "destek_disi", baslik: texts.destek_disi.baslik },
  // added later by the written rule (docs/demo_example_cases.md): REJECTED + plan, KOSULLU strongest
  { key: "ret_kosullu", tur: "ret_plan", baslik: texts.karar.REJECTED.baslik },
];

for (const c of CASES) {
  test(`örnek vaka "${c.key}" doğru sonuç sayfasını açar ve uyarı şeridi görünür`, async ({ page }) => {
    await page.goto("/");
    await page.locator(`[data-ornek="${c.key}"]`).click();
    const sayfa = page.locator(`[data-sonuc-turu="${c.tur}"]`);
    await expect(sayfa).toBeVisible();
    await expect(sayfa.getByRole("heading", { name: c.baslik, level: 2 })).toBeVisible();
    await seritVar(page);
    await shot(page, `sonuc-${c.key}`);
  });
}

test("ret + plan: yollar, USD maliyet ve süre 'varsayım' etiketli, kurum eylemi 'karşı teklif'", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-ornek="ret_plan"]').click();
  const plan = page.locator('[data-plan="PLAN"]');
  await expect(plan).toBeVisible();
  const yollar = plan.locator("[data-yol]");
  await expect(yollar.first()).toBeVisible();
  for (const y of await yollar.all()) {
    await expect(y).toContainText(texts.plan.maliyet);
    await expect(y).toContainText(texts.plan.usd);
    await expect(y.locator("dl .etiket")).toHaveText(["varsayım", "varsayım"]);
  }
  for (const y of await yollar.all()) {
    // resilience label, the agreed sufficiency sentence (percent comes from the API), evidence
    await expect(y.locator("[data-dayaniklilik]")).toHaveAttribute(
      "data-dayaniklilik",
      /^(GUCLU|KOSULLU|ZAYIF)$/,
    );
    await expect(y.locator("[data-yeterlilik]")).toHaveText(
      /^Bu planın yeterli olması için modelin öngördüğü etkinin en az %\d+ kadarının gerçekleşmesi gerekir\.$/,
    );
    await expect(y.locator("[data-kanit]")).toContainText(texts.kanit.M);
  }
  await expect(plan.locator("[data-kanit]").first()).toContainText(texts.kanit_meta.risk);
  await expect(plan).toContainText(texts.dayaniklilik_meta.esik_notu);
  const kurumlu = plan.locator('[data-yol="institution"], [data-yol="hybrid"]');
  if ((await kurumlu.count()) > 0) {
    await expect(kurumlu.first()).toContainText("Karşı teklif");
  }
});

test("ret + koşullu etiket: en güçlü yolun etiketi KOSULLU, cümle ve kanıt rozetleri görünür", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-ornek="ret_kosullu"]').click();
  const plan = page.locator('[data-plan="PLAN"]');
  await expect(plan).toBeVisible();
  await expect(plan.locator('[data-dayaniklilik="KOSULLU"]').first()).toBeVisible();
  await expect(plan.locator("[data-yeterlilik]").first()).toHaveText(
    /^Bu planın yeterli olması için modelin öngördüğü etkinin en az %\d+ kadarının gerçekleşmesi gerekir\.$/,
  );
  await expect(plan.locator("[data-kanit]").first()).toContainText(texts.kanit.M);
  await shot(page, "sonuc-ret_kosullu");
});

const fmtTr = (n: number) => new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 4 }).format(n);

for (const key of ["ret_plan", "ret_plan_yok"]) {
  test(`güvenlik payı (${key}): API değeri, 'varsayım' etiketi ve kaynak ADR-007 sonuç sayfasında`, async ({ page }) => {
    await page.goto("/");
    const [yanit] = await Promise.all([
      page.waitForResponse((r) => r.url().endsWith("/score")),
      page.locator(`[data-ornek="${key}"]`).click(),
    ]);
    const pay = (await yanit.json()).guvenlik_payi;
    expect(pay.etiket).toBe("varsayım");
    expect(pay.kaynak).toBe("ADR-007");
    const kart = page.locator("[data-guvenlik-payi]");
    await expect(kart).toBeVisible();
    await expect(kart.locator("[data-guvenlik-payi-deger]")).toHaveText(fmtTr(pay.deger));
    await expect(kart).toContainText("varsayım");
    await expect(kart).toContainText("ADR-007");
    await expect(kart).toContainText(texts.guvenlik_payi.baslik);
  });
}

test("güvenlik payı: onay sayfasında (plan yok/gerekmiyor) gösterilmez", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-ornek="onay"]').click();
  await expect(page.locator("[data-sonuc-turu]")).toBeVisible();
  await expect(page.locator("[data-guvenlik-payi]")).toHaveCount(0);
});

test("ret + PLAN_YOK: bağlayıcı kısıtlar ve eşiğe uzaklık var, plan/maliyet/süre yok", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-ornek="ret_plan_yok"]').click();
  const bolum = page.locator('[data-plan="PLAN_YOK"]');
  await expect(bolum).toBeVisible();
  await expect(bolum).toContainText(texts.plan_yok.kisitlar_baslik);
  await expect(bolum).toContainText(texts.plan_yok.uzaklik_baslik);
  await expect(page.locator("[data-yol]")).toHaveCount(0);
  await expect(page.locator("[data-dayaniklilik]")).toHaveCount(0);
  await expect(page.getByText(texts.plan.maliyet)).toHaveCount(0);
  await expect(page.getByText(texts.plan.sure)).toHaveCount(0);
});

test("değerlendirilemez sayfası ihlal eden alanı gösterir, skor ve plan göstermez", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-ornek="destek_disi"]').click();
  await expect(page.locator('[data-ihlal="application_type"]')).toBeVisible();
  await expect(page.locator("[data-plan]")).toHaveCount(0);
  await expect(page.getByText(texts.sonuc.skor_baslik)).toHaveCount(0);
});

test("10 satırlık CSV: portföy özeti, satır tablosu, sonuç CSV indirme, uyarı şeridi", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-sekme="toplu"]').click();
  await page.setInputFiles("#csv-dosya", SAMPLE_CSV);
  await page.getByRole("button", { name: texts.toplu.yukle }).click();
  await expect(page.locator('[data-ozet="n"]')).toHaveText("10");
  await seritVar(page);
  await expect(page.locator('[data-toplu="ozet"]')).toContainText(texts.toplu.kova_baslik);
  const pay = page.locator("[data-guvenlik-payi]");
  await expect(pay).toBeVisible();
  await expect(pay.locator("[data-guvenlik-payi-deger]")).toHaveText(/^\d+,\d+$/);
  await expect(pay).toContainText("ADR-007");
  const et = page.locator('[data-toplu="dayaniklilik"]');
  await expect(et).toContainText(texts.toplu_dayaniklilik.baslik);
  await expect(et).toContainText(texts.toplu_dayaniklilik.yol_baslik);
  await expect(page.locator('[data-toplu="satirlar"] tbody tr')).toHaveCount(10);
  await shot(page, "toplu-ozet");

  const [indirme] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: texts.toplu.sonuc_indir }).click(),
  ]);
  const path = await indirme.path();
  const satirlar = readFileSync(path, "utf8").trim().split("\n");
  expect(satirlar).toHaveLength(11);
  expect(satirlar[0].startsWith("satir_no,kayit_id,dis_durum")).toBe(true);
  expect(satirlar[0]).toContain("customer_min_phi");
  expect(satirlar[0]).toContain("institution_dayaniklilik");
});

test("hatalı CSV reddedilir, kısmi sonuç gösterilmez", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-sekme="toplu"]').click();
  await page.setInputFiles("#csv-dosya", {
    name: "bozuk.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("loan_amnt,dti\n1000,5\n"),
  });
  await page.getByRole("button", { name: texts.toplu.yukle }).click();
  await expect(page.locator('[data-toplu="hata"]')).toContainText(texts.toplu.hata_baslik);
  await expect(page.locator('[data-toplu="ozet"]')).toHaveCount(0);
});

test("form: boş tarih ve geçersiz sayı istemci tarafında reddedilir", async ({ page }) => {
  await page.goto("/");
  await page.locator("#loan_amnt").fill("abc");
  await page.getByRole("button", { name: texts.form.hesapla, exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(texts.form.tarih_hatasi);
  await expect(page.getByRole("alert")).toContainText(texts.form.sayi_hatasi);
  await shot(page, "form");
});
