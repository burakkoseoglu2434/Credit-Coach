import { fmtSayi, fmtTam } from "../format";
import texts from "../texts.json";
import type { Alan, OuterStatus, PlanVar, PlanYok, PublicReasonCode, ScoreResponse, YolPlan } from "../types";

const kararMeta: Record<OuterStatus, { baslik: string; aciklama: string }> = texts.karar;
const gerekce: Record<PublicReasonCode, string> = texts.gerekce;
const alanEtiket: Record<Alan, { etiket: string }> = texts.alanlar;
const kisit: Record<string, string> = texts.kisit;
const yolAd: Record<string, string> = texts.yol;
const eylemAd: Record<string, string> = texts.eylem;
const seviyeAd: Record<string, string> = texts.seviye;
const kosul: Record<string, string> = texts.kosul;

export type SonucTuru = "onay" | "kosullu" | "ret_plan" | "ret_plan_yok" | "destek_disi";

/** Which page the response opens (a classification of the API answer, no arithmetic). */
export function sonucTuru(r: ScoreResponse): SonucTuru {
  const k = r.karar;
  if (k.destek_ihlalleri.length > 0) return "destek_disi";
  if (k.dis_durum === "APPROVED") return "onay";
  if (k.dis_durum === "CONDITIONAL") return "kosullu";
  return k.plan.durum === "PLAN" ? "ret_plan" : "ret_plan_yok";
}

function Skor({ r }: { r: ScoreResponse }) {
  const s = r.karar.skor;
  if (!s) return null;
  return (
    <div className="karti">
      <h3>{texts.sonuc.skor_baslik}</h3>
      <dl>
        <dt>{texts.sonuc.skor_alt}</dt>
        <dd>{fmtSayi(s.p_low)}</dd>
        <dt>{texts.sonuc.skor_nokta}</dt>
        <dd>{fmtSayi(s.p_point)}</dd>
        <dt>{texts.sonuc.skor_ust}</dt>
        <dd>{fmtSayi(s.p_high)}</dd>
      </dl>
    </div>
  );
}

function Gerekceler({ kodlar }: { kodlar: PublicReasonCode[] }) {
  return (
    <div className="karti">
      <h3>{texts.sonuc.gerekce_baslik}</h3>
      <ul>
        {kodlar.map((c) => (
          <li key={c}>
            <code>{c}</code>: {gerekce[c]}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Surumler({ r }: { r: ScoreResponse }) {
  const s = r.surumler;
  return (
    <details className="karti">
      <summary>{texts.sonuc.surumler_baslik}</summary>
      <dl>
        <dt>{texts.sonuc.surum_politika}</dt>
        <dd>
          {s.politika_surumu} <code>{s.politika_sha256}</code>
        </dd>
        <dt>{texts.sonuc.surum_katalog}</dt>
        <dd>
          {s.katalog_surumu} <code>{s.katalog_sha256}</code>
        </dd>
        <dt>{texts.sonuc.surum_bundle}</dt>
        <dd>
          <code>{s.bundle_sha256}</code>
        </dd>
        <dt>{texts.sonuc.surum_destek}</dt>
        <dd>
          <code>{s.support_sha256}</code>
        </dd>
      </dl>
    </details>
  );
}

function YolKarti({ y }: { y: YolPlan }) {
  return (
    <article className="karti" data-yol={y.yol_tipi}>
      <h4>{yolAd[y.yol_tipi] ?? y.yol_tipi}</h4>
      <h5>{texts.plan.eylemler}</h5>
      <ul>
        {y.eylemler.map(([e, s]) => (
          <li key={`${e}-${s}`}>
            <strong>{eylemAd[e] ?? e}</strong>: {seviyeAd[s] ?? s}
          </li>
        ))}
      </ul>
      <dl>
        <dt>{texts.plan.maliyet}</dt>
        <dd>
          {fmtTam(y.maliyet_usd)} {texts.plan.usd} <span className="etiket">{y.maliyet_etiketi}</span>
        </dd>
        <dt>{texts.plan.sure}</dt>
        <dd>
          {y.sure_hafta[0]}-{y.sure_hafta[1]} {texts.plan.hafta}{" "}
          <span className="etiket">{y.sure_etiketi}</span>
        </dd>
        <dt>{texts.plan.sonrasi}</dt>
        <dd>
          {fmtSayi(y.p_low)} / {fmtSayi(y.p_point)} / {fmtSayi(y.p_high)}
        </dd>
        {y.kirpildi.length > 0 && (
          <>
            <dt>{texts.plan.kirpildi}</dt>
            <dd>{y.kirpildi.map((a) => alanEtiket[a as Alan]?.etiket ?? a).join(", ")}</dd>
          </>
        )}
      </dl>
    </article>
  );
}

function PlanBolumu({ plan }: { plan: PlanVar }) {
  return (
    <section data-plan="PLAN">
      <h3>{texts.plan.baslik}</h3>
      <p>{texts.plan.not}</p>
      <p className="not">{texts.plan.yollar_not}</p>
      <div className="kart-ikili">
        {plan.yollar.map((y) => (
          <YolKarti key={y.yol_tipi} y={y} />
        ))}
      </div>
      <p className="not">{texts.plan.varsayim}</p>
    </section>
  );
}

function PlanYokBolumu({ plan }: { plan: PlanYok }) {
  return (
    <section data-plan="PLAN_YOK">
      <h3>{texts.plan_yok.baslik}</h3>
      <p>{texts.plan_yok.aciklama}</p>
      <h4>{texts.plan_yok.kisitlar_baslik}</h4>
      <ul>
        {plan.bagli_kisitlar.map(([e, nedenler]) => (
          <li key={e}>
            <strong>{eylemAd[e] ?? e}</strong>
            <ul>
              {nedenler.map((n) => (
                <li key={n}>{kisit[n] ?? n}</li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
      {plan.esige_uzaklik !== null && plan.esige_uzaklik !== undefined && (
        <>
          <h4>{texts.plan_yok.uzaklik_baslik}</h4>
          <p>
            {fmtSayi(plan.esige_uzaklik)} <span className="not">{texts.plan_yok.uzaklik_aciklama}</span>
          </p>
        </>
      )}
    </section>
  );
}

function DestekDisi({ r }: { r: ScoreResponse }) {
  return (
    <section data-sayfa-turu="destek_disi">
      <h2 className="karar-baslik karar-DEGERLENDIRILEMEZ">{texts.destek_disi.baslik}</h2>
      <p>{texts.destek_disi.aciklama}</p>
      <h3>{texts.destek_disi.alanlar_baslik}</h3>
      <ul>
        {r.karar.destek_ihlalleri.map((a) => (
          <li key={a} data-ihlal={a}>
            {alanEtiket[a as Alan]?.etiket ?? a} <code>{a}</code>
          </li>
        ))}
      </ul>
      <p>{texts.destek_disi.sonraki}</p>
      <Gerekceler kodlar={r.karar.gerekce_kodlari} />
    </section>
  );
}

export default function Sonuc({ r }: { r: ScoreResponse }) {
  const tur = sonucTuru(r);
  const k = r.karar;
  return (
    <div data-sonuc-turu={tur}>
      {tur === "destek_disi" ? (
        <DestekDisi r={r} />
      ) : (
        <>
          <section>
            <p className="not">{texts.sonuc.karar_baslik}</p>
            <h2 className={`karar-baslik karar-${k.dis_durum}`}>{kararMeta[k.dis_durum].baslik}</h2>
            <p>{kararMeta[k.dis_durum].aciklama}</p>
            {k.conditional_type && <p>{kosul[k.conditional_type] ?? k.conditional_type}</p>}
            {k.upgrade_condition && <p>{kosul[k.upgrade_condition] ?? k.upgrade_condition}</p>}
            <p className="not">{texts.sonuc.karar_notu}</p>
          </section>
          <Skor r={r} />
          <Gerekceler kodlar={k.gerekce_kodlari} />
          {k.plan.durum === "PLAN" && <PlanBolumu plan={k.plan as PlanVar} />}
          {k.plan.durum === "PLAN_YOK" && <PlanYokBolumu plan={k.plan as PlanYok} />}
          {k.plan.durum === "PLAN_GEREKSIZ" && (
            <section data-plan="PLAN_GEREKSIZ">
              <p>{texts.plan.gereksiz}</p>
            </section>
          )}
        </>
      )}
      <Surumler r={r} />
      <details className="karti">
        <summary>{texts.sonuc.ham_veri}</summary>
        <pre>{JSON.stringify(r, null, 2)}</pre>
      </details>
    </div>
  );
}
