import type { FormEvent } from "react";
import { alanTuru } from "../fields";
import texts from "../texts.json";
import type { Alan, Basvuru } from "../types";

export type FormDurumu = { alanlar: Record<Alan, string>; tarih: string };

const alanMeta: Record<Alan, { etiket: string; birim: string }> = texts.alanlar;
const secenekler: Partial<Record<Alan, { deger: string; etiket: string }[]>> = texts.secenekler;
const bolumAlanlari = texts.bolum_alanlari as Record<keyof typeof texts.bolumler, Alan[]>;

export const bosForm = (): FormDurumu => ({
  alanlar: Object.fromEntries(
    (Object.keys(alanTuru) as Alan[]).map((a) => [a, ""]),
  ) as Record<Alan, string>,
  tarih: "",
});

/** Raw API record -> form strings (no arithmetic: String() / trim() only). */
export function formdanBasvuru(b: Basvuru, tarih: string): FormDurumu {
  const f = bosForm();
  for (const a of Object.keys(alanTuru) as Alan[]) {
    const v = b[a];
    f.alanlar[a] = v === null ? "" : String(v).trim();
  }
  f.tarih = tarih;
  return f;
}

export type Gonderi = { basvuru: Basvuru; tarih: string } | { hatalar: string[] };

/** Form strings -> request. Numbers are converted, never computed. */
export function gonderiHazirla(f: FormDurumu): Gonderi {
  const hatalar: string[] = [];
  const out: Record<string, number | string | null> = {};
  for (const a of Object.keys(alanTuru) as Alan[]) {
    const v = f.alanlar[a].trim();
    if (v === "") {
      out[a] = null;
    } else if (alanTuru[a] === "sayi") {
      const n = Number(v);
      if (Number.isNaN(n)) hatalar.push(`${alanMeta[a].etiket}: ${texts.form.sayi_hatasi}`);
      out[a] = n;
    } else {
      out[a] = v;
    }
  }
  if (f.tarih === "") hatalar.push(texts.form.tarih_hatasi);
  if (hatalar.length > 0) return { hatalar };
  return { basvuru: out as Basvuru, tarih: f.tarih };
}

type Props = {
  durum: FormDurumu;
  onChange: (d: FormDurumu) => void;
  onSubmit: () => void;
  onTemizle: () => void;
  yukleniyor: boolean;
  hatalar: string[];
};

export default function Form({ durum, onChange, onSubmit, onTemizle, yukleniyor, hatalar }: Props) {
  const set = (a: Alan, v: string) =>
    onChange({ ...durum, alanlar: { ...durum.alanlar, [a]: v } });

  const gonder = (e: FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form onSubmit={gonder} className="form" aria-label={texts.form.baslik}>
      <h2>{texts.form.baslik}</h2>
      <div className="alan tarih">
        <label htmlFor="basvuru_tarihi">{texts.form.tarih}</label>
        <input
          id="basvuru_tarihi"
          type="date"
          value={durum.tarih}
          onChange={(e) => onChange({ ...durum, tarih: e.target.value })}
        />
        <small>{texts.form.tarih_not}</small>
      </div>
      {(Object.keys(bolumAlanlari) as (keyof typeof texts.bolumler)[]).map((b) => (
        <fieldset key={b}>
          <legend>{texts.bolumler[b]}</legend>
          <div className="grid">
            {bolumAlanlari[b].map((a) => {
              const meta = alanMeta[a];
              const birim = (texts.birimler as Record<string, string>)[meta.birim];
              const opts = secenekler[a];
              return (
                <div className="alan" key={a}>
                  <label htmlFor={a}>
                    {meta.etiket}
                    {birim ? <span className="birim"> ({birim})</span> : null}
                  </label>
                  {alanTuru[a] === "secim" && opts ? (
                    <select id={a} value={durum.alanlar[a]} onChange={(e) => set(a, e.target.value)}>
                      <option value="">{texts.form.bos_birak}</option>
                      {opts.map((o) => (
                        <option key={o.deger} value={o.deger}>
                          {o.etiket}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      id={a}
                      type="text"
                      inputMode={alanTuru[a] === "sayi" ? "decimal" : "text"}
                      value={durum.alanlar[a]}
                      onChange={(e) => set(a, e.target.value)}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </fieldset>
      ))}
      {hatalar.length > 0 && (
        <div role="alert" className="hata">
          <strong>{texts.form.api_hatasi}</strong>
          <ul>
            {hatalar.map((h) => (
              <li key={h}>{h}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="satir">
        <button type="submit" className="birincil" disabled={yukleniyor}>
          {yukleniyor ? texts.form.hesaplaniyor : texts.form.hesapla}
        </button>
        <button type="button" onClick={onTemizle}>
          {texts.form.temizle}
        </button>
      </div>
    </form>
  );
}
