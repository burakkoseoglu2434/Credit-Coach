import { useState } from "react";
import { ApiError, postScore } from "./api/client";
import Form, {
  bosForm,
  type FormDurumu,
  formdanBasvuru,
  gonderiHazirla,
} from "./components/Form";
import Ornekler, { type Ornek } from "./components/Ornekler";
import Sonuc from "./components/Sonuc";
import Toplu from "./components/Toplu";
import texts from "./texts.json";
import type { ScoreResponse } from "./types";

import "./styles.css";

export default function App() {
  const [form, setForm] = useState<FormDurumu>(bosForm());
  const [sonuc, setSonuc] = useState<ScoreResponse | null>(null);
  const [hatalar, setHatalar] = useState<string[]>([]);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [sekme, setSekme] = useState<"tek" | "toplu">("tek");

  async function degerlendir(f: FormDurumu) {
    const g = gonderiHazirla(f);
    if ("hatalar" in g) {
      setHatalar(g.hatalar);
      return;
    }
    setHatalar([]);
    setYukleniyor(true);
    try {
      setSonuc(await postScore({ basvuru: g.basvuru, basvuru_tarihi: g.tarih }));
    } catch (e) {
      setHatalar(e instanceof ApiError ? e.detail : [texts.form.sunucu_hatasi]);
    } finally {
      setYukleniyor(false);
    }
  }

  function ornekSec(o: Ornek) {
    const f = formdanBasvuru(o.basvuru, o.basvuru_tarihi);
    setForm(f);
    void degerlendir(f);
  }

  return (
    <main>
      <header>
        <h1>{texts.uygulama.baslik}</h1>
        <p>{texts.uygulama.altbaslik}</p>
      </header>
      <nav className="satir" role="tablist">
        {(["tek", "toplu"] as const).map((s) => (
          <button
            key={s}
            type="button"
            role="tab"
            aria-selected={sekme === s}
            data-sekme={s}
            className={sekme === s ? "birincil" : ""}
            onClick={() => setSekme(s)}
          >
            {texts.sekmeler[s]}
          </button>
        ))}
      </nav>
      {sekme === "toplu" ? (
        <Toplu />
      ) : sonuc ? (
        <section data-sayfa="sonuc">
          <h2>{texts.sonuc.baslik}</h2>
          <button type="button" onClick={() => setSonuc(null)}>
            {texts.sonuc.geri}
          </button>
          <Sonuc r={sonuc} />
        </section>
      ) : (
        <>
          <Ornekler onSec={ornekSec} />
          <Form
            durum={form}
            onChange={setForm}
            onSubmit={() => void degerlendir(form)}
            onTemizle={() => {
              setForm(bosForm());
              setHatalar([]);
            }}
            yukleniyor={yukleniyor}
            hatalar={hatalar}
          />
        </>
      )}
    </main>
  );
}
