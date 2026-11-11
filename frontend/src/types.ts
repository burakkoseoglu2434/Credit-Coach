import type { components } from "./api/schema";

type S = components["schemas"];
export type Basvuru = S["Basvuru"];
export type ScoreRequest = S["ScoreRequest"];
export type ScoreResponse = S["ScoreResponse"];
export type SatirKarari = S["SatirKarari"];
export type BatchResponse = S["BatchResponse"];
export type PublicReasonCode = S["PublicReasonCode"];
export type OuterStatus = S["OuterStatus"];
export type PlanVar = S["PlanVar"];
export type PlanYok = S["PlanYok"];
export type YolPlan = S["YolPlan"];
export type PortfoyOzeti = S["PortfoyOzeti"];
export type Alan = keyof Basvuru;
