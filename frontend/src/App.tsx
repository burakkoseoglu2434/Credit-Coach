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
import texts from "./texts.json";
import type { ScoreResponse } from "./types";

import "./styles.css";

export default function App() {
  const [form, setForm] = useState<FormDurumu>(bosForm());
  const [sonuc, setSonuc] = useState<ScoreResponse | null>(null);
  const [hatalar, setHatalar] = useState<string[]>([]);
  const [yukleniyor, setYukleniyor] = useState(false);

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
      {sonuc ? (
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
