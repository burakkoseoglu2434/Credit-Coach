import { fmtSayi } from "../format";
import texts from "../texts.json";
import type { components } from "../api/schema";

type Pay = components["schemas"]["GuvenlikPayi"];

/** Safety margin as returned by the API (value, "varsayım" label, source): shown, never computed. */
export default function GuvenlikPayi({ pay }: { pay: Pay }) {
  return (
    <div className="karti" data-guvenlik-payi>
      <h3>{texts.guvenlik_payi.baslik}</h3>
      <p>
        <strong data-guvenlik-payi-deger>{fmtSayi(pay.deger)}</strong>{" "}
        <span className="etiket">{pay.etiket}</span>
      </p>
      <p className="not">{texts.guvenlik_payi.aciklama}</p>
      <p className="not">
        {texts.guvenlik_payi.kaynak}: {pay.kaynak}. {texts.guvenlik_payi.turetme}
      </p>
    </div>
  );
}
