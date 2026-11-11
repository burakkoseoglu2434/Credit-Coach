/** Presentation only: the UI never computes a number, it formats what the API returned. */
const sayi = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 4 });
const tam = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
const yuzde = new Intl.NumberFormat("tr-TR", { style: "percent", maximumFractionDigits: 1 });

export const fmtSayi = (n: number): string => sayi.format(n);
export const fmtTam = (n: number): string => tam.format(n);
export const fmtYuzde = (n: number | null): string => (n === null ? "-" : yuzde.format(n));
