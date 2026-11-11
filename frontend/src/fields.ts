import type { Alan } from "./types";

export type AlanTuru = "sayi" | "secim" | "metin";

/** Compile-time complete: a new API field without an entry here fails the type check. */
export const alanTuru: Record<Alan, AlanTuru> = {
  acc_now_delinq: "sayi",
  acc_open_past_24mths: "sayi",
  annual_inc: "sayi",
  application_type: "secim",
  chargeoff_within_12_mths: "sayi",
  collections_12_mths_ex_med: "sayi",
  delinq_2yrs: "sayi",
  delinq_amnt: "sayi",
  dti: "sayi",
  earliest_cr_line: "metin",
  emp_length: "secim",
  fico_range_high: "sayi",
  fico_range_low: "sayi",
  home_ownership: "secim",
  inq_last_6mths: "sayi",
  loan_amnt: "sayi",
  mort_acc: "sayi",
  open_acc: "sayi",
  pub_rec: "sayi",
  pub_rec_bankruptcies: "sayi",
  purpose: "secim",
  revol_bal: "sayi",
  revol_util: "sayi",
  tax_liens: "sayi",
  term: "secim",
  tot_coll_amt: "sayi",
  tot_cur_bal: "sayi",
  tot_hi_cred_lim: "sayi",
  total_acc: "sayi",
  total_bal_ex_mort: "sayi",
  total_bc_limit: "sayi",
  total_rev_hi_lim: "sayi",
};
