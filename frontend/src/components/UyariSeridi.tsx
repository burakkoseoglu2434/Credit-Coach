import texts from "../texts.json";

/** Fixed warning strip: rendered on every result page (single and batch). */
export default function UyariSeridi() {
  return (
    <div className="serit" role="note" data-uyari-seridi>
      {texts.uyari}
      <div className="kurgu">{texts.kurgu}</div>
    </div>
  );
}
