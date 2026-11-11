import { useState } from "react";
import { ApiError, postBatch } from "../api/client";
import { sonucCsv } from "../csv";
import { fmtTam, fmtYuzde } from "../format";
import texts from "../texts.json";
import type { BatchResponse } from "../types";
import UyariSeridi from "./UyariSeridi";

const dagilim: Record<string, string> = texts.dagilim;
const planDurumu: Record<string, string> = texts.plan_durumu;
const yolAd: Record<string, string> = texts.yol;
const dayaniklilik: Record<string, { ad: string }> = texts.dayaniklilik;
const ADIM = 100;

function indir(ad: string, metin: string) {
  const url = URL.createObjectURL(new Blob([metin], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = ad;
  a.click();
  URL.revokeObjectURL(url);
}

function Ozet({ o }: { o: BatchResponse["ozet"] }) {
  return (
    <section data-toplu="ozet">
      <h2>{texts.toplu.ozet_baslik}</h2>
      <dl>
        <dt>{texts.toplu.n}</dt>
        <dd data-ozet="n">{fmtTam(o.n)}</dd>
        <dt>{texts.toplu.destek_disi}</dt>
        <dd data-ozet="destek_disi">{fmtTam(o.destek_disi)}</dd>
        <dt>{texts.toplu.plan_arayan}</dt>
        <dd data-ozet="plan_arayan">{fmtTam(o.plan_arayan)}</dd>
        <dt>{texts.toplu.plan_orani}</dt>
        <dd data-ozet="gecerli_plan_orani">{fmtYuzde(o.gecerli_plan_orani)}</dd>
      </dl>
      <div className="kart-ikili">
        <div className="karti">
          <h3>{texts.toplu.dagilim_baslik}</h3>
          <table>
            <tbody>
              {Object.entries(o.dis_durum_dagilimi).map(([k, v]) => (
                <tr key={k}>
                  <td>{dagilim[k] ?? k}</td>
                  <td>{fmtTam(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="karti">
          <h3>{texts.toplu.plan_dagilim_baslik}</h3>
          <table>
            <tbody>
              {Object.entries(o.plan_durumu_dagilimi).map(([k, v]) => (
                <tr key={k}>
                  <td>{planDurumu[k] ?? k}</td>
                  <td>{fmtTam(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="karti">
          <h3>{texts.toplu.yol_orani_baslik}</h3>
          <table>
            <tbody>
              {Object.entries(o.yol_orani).map(([k, v]) => (
                <tr key={k}>
                  <td>{yolAd[k] ?? k}</td>
                  <td>{fmtYuzde(v ?? null)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="karti" data-toplu="dayaniklilik">
        <h3>{texts.toplu_dayaniklilik.baslik}</h3>
        <table>
          <tbody>
            {Object.entries(o.dayaniklilik_dagilimi).map(([k, v]) => (
              <tr key={k}>
                <td>{dayaniklilik[k]?.ad ?? k}</td>
                <td>{fmtTam(v)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <h3>{texts.toplu_dayaniklilik.yol_baslik}</h3>
        <table>
          <thead>
            <tr>
              <th>{texts.toplu_dayaniklilik.yol}</th>
              {Object.keys(dayaniklilik).map((k) => (
                <th key={k}>{dayaniklilik[k].ad}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(o.yol_dayaniklilik).map(([yol, dist]) => (
              <tr key={yol}>
                <td>{yolAd[yol] ?? yol}</td>
                {["GUCLU", "KOSULLU", "ZAYIF"].map((k) => (
                  <td key={k}>{fmtTam(dist[k] ?? 0)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="karti">
        <h3>{texts.toplu.kova_baslik}</h3>
        <table>
          <thead>
            <tr>
              <th>{texts.toplu.kova}</th>
              <th>{texts.toplu.kova_n}</th>
              <th>{texts.toplu.kova_oran}</th>
            </tr>
          </thead>
          <tbody>
            {o.kovalar.map((k) => (
              <tr key={k.kova}>
                <td>{k.kova}</td>
                <td>{fmtTam(k.n)}</td>
                <td>{fmtYuzde(k.gecerli_plan_orani ?? null)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function Toplu() {
  const [sonuc, setSonuc] = useState<BatchResponse | null>(null);
  const [hatalar, setHatalar] = useState<string[]>([]);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [dosya, setDosya] = useState<File | null>(null);
  const [gorunen, setGorunen] = useState(ADIM);

  async function yukle() {
    if (!dosya) return;
    setYukleniyor(true);
    setHatalar([]);
    setSonuc(null);
    setGorunen(ADIM);
    try {
      setSonuc(await postBatch(await dosya.text()));
    } catch (e) {
      setHatalar(e instanceof ApiError ? e.detail : [texts.form.sunucu_hatasi]);
    } finally {
      setYukleniyor(false);
    }
  }

  return (
    <div data-sayfa="toplu">
      <section>
        <h2>{texts.toplu.baslik}</h2>
        <p>{texts.toplu.aciklama}</p>
        <div className="satir">
          <label htmlFor="csv-dosya">{texts.toplu.dosya}</label>
          <input
            id="csv-dosya"
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setDosya(e.target.files?.[0] ?? null)}
          />
          <button type="button" className="birincil" disabled={!dosya || yukleniyor} onClick={() => void yukle()}>
            {yukleniyor ? texts.toplu.bekle : texts.toplu.yukle}
          </button>
          <a href="/ornek_toplu.csv" download="ornek_toplu.csv">
            {texts.toplu.ornek_indir}
          </a>
        </div>
      </section>
      {hatalar.length > 0 && (
        <div role="alert" className="hata" data-toplu="hata">
          <strong>{texts.toplu.hata_baslik}</strong> {texts.toplu.hata_not}
          <ul>
            {hatalar.map((h) => (
              <li key={h}>{h}</li>
            ))}
          </ul>
        </div>
      )}
      {!sonuc && hatalar.length === 0 && <p className="not">{texts.toplu.bos}</p>}
      {sonuc && (
        <>
          <UyariSeridi />
          <Ozet o={sonuc.ozet} />
          <section data-toplu="satirlar">
            <h2>{texts.toplu.satirlar_baslik}</h2>
            <div className="satir">
              <button type="button" onClick={() => indir("sonuc.csv", sonucCsv(sonuc.satirlar))}>
                {texts.toplu.sonuc_indir}
              </button>
              <span className="not">{texts.toplu.tumu}</span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>{texts.toplu.satir_no}</th>
                  <th>{texts.toplu.kayit_id}</th>
                  <th>{texts.toplu.karar}</th>
                  <th>{texts.toplu.plan_durumu}</th>
                  <th>{texts.toplu.yollar}</th>
                  <th>{texts.toplu.destek_ihlalleri}</th>
                </tr>
              </thead>
              <tbody>
                {sonuc.satirlar.slice(0, gorunen).map((s) => (
                  <tr key={s.satir_no}>
                    <td>{s.satir_no}</td>
                    <td>{s.kayit_id ?? ""}</td>
                    <td>{dagilim[s.karar.dis_durum] ?? s.karar.dis_durum}</td>
                    <td>{planDurumu[s.karar.plan.durum] ?? s.karar.plan.durum}</td>
                    <td>
                      {s.karar.plan.durum === "PLAN"
                        ? s.karar.plan.yollar.map((y) => yolAd[y.yol_tipi] ?? y.yol_tipi).join(", ")
                        : ""}
                    </td>
                    <td>{s.karar.destek_ihlalleri.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {gorunen < sonuc.satirlar.length && (
              <button type="button" onClick={() => setGorunen(gorunen + ADIM)}>
                {texts.toplu.daha_fazla}
              </button>
            )}
          </section>
        </>
      )}
    </div>
  );
}
