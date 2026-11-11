import ornekler from "../ornekler.json";
import texts from "../texts.json";
import type { Basvuru } from "../types";

export type Ornek = {
  anahtar: keyof typeof texts.ornek_vakalar;
  kaynak_id: string;
  varyant: boolean;
  basvuru: Basvuru;
  basvuru_tarihi: string;
};

export const ORNEKLER = ornekler as unknown as Ornek[];

export default function Ornekler({ onSec }: { onSec: (o: Ornek) => void }) {
  return (
    <section className="ornekler" aria-label={texts.form.ornekler_baslik}>
      <h2>{texts.form.ornekler_baslik}</h2>
      <p className="not">{texts.form.ornekler_not}</p>
      <div className="satir">
        {ORNEKLER.map((o) => (
          <button
            key={o.anahtar}
            type="button"
            data-ornek={o.anahtar}
            onClick={() => onSec(o)}
            title={texts.ornek_vakalar[o.anahtar].aciklama}
          >
            <strong>{texts.ornek_vakalar[o.anahtar].ad}</strong>
            <span>{texts.ornek_vakalar[o.anahtar].aciklama}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
