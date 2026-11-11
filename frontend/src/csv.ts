import type { SatirKarari } from "./types";

type Satir = { satir_no: number; kayit_id?: string | null; karar: SatirKarari };

const YOLLAR = ["customer", "hybrid", "institution"] as const;

const kacis = (v: string): string => (/[",\n\r]/.test(v) ? `"${v.replaceAll('"', '""')}"` : v);

export const SONUC_BASLIK: string[] = [
  "satir_no",
  "kayit_id",
  "dis_durum",
  "gerekce_kodlari",
  "destek_ihlalleri",
  "p_low",
  "p_point",
  "p_high",
  "plan_durumu",
  "esige_uzaklik",
  ...YOLLAR.flatMap((y) => [
    `${y}_plan_id`,
    `${y}_maliyet_usd`,
    `${y}_sure_hafta`,
    `${y}_min_phi`,
    `${y}_dayaniklilik`,
  ]),
];

/** Result rows -> CSV text. Strings are copied from the API answer; nothing is computed. */
export function sonucCsv(satirlar: Satir[]): string {
  const out: string[] = [SONUC_BASLIK.join(",")];
  for (const s of satirlar) {
    const k = s.karar;
    const plan = k.plan;
    const yol = (t: string) =>
      plan.durum === "PLAN" ? plan.yollar.find((y) => y.yol_tipi === t) : undefined;
    const hucreler: string[] = [
      String(s.satir_no),
      s.kayit_id ?? "",
      k.dis_durum,
      k.gerekce_kodlari.join(";"),
      k.destek_ihlalleri.join(";"),
      k.skor ? String(k.skor.p_low) : "",
      k.skor ? String(k.skor.p_point) : "",
      k.skor ? String(k.skor.p_high) : "",
      plan.durum,
      plan.durum === "PLAN_YOK" && plan.esige_uzaklik != null ? String(plan.esige_uzaklik) : "",
      ...YOLLAR.flatMap((t) => {
        const y = yol(t);
        return y
          ? [
              y.plan_id,
              String(y.maliyet_usd),
              `${y.sure_hafta[0]}-${y.sure_hafta[1]}`,
              String(y.min_phi),
              y.dayaniklilik,
            ]
          : ["", "", "", "", ""];
      }),
    ];
    out.push(hucreler.map(kacis).join(","));
  }
  return `${out.join("\n")}\n`;
}
