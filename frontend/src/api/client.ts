import type { BatchResponse, ScoreRequest, ScoreResponse } from "../types";

export class ApiError extends Error {
  status: number;
  detail: string[];
  constructor(status: number, detail: string[]) {
    super(detail.join("; "));
    this.status = status;
    this.detail = detail;
  }
}

async function ayikla(res: Response): Promise<string[]> {
  try {
    const body = await res.json();
    const d = body?.detail;
    if (Array.isArray(d)) {
      return d.map((e) =>
        typeof e === "string" ? e : `${(e.loc ?? []).join(".")}: ${e.msg}`,
      );
    }
    if (typeof d === "string") return [d];
  } catch {
    /* body is not JSON */
  }
  return [`HTTP ${res.status}`];
}

export async function postScore(req: ScoreRequest): Promise<ScoreResponse> {
  const res = await fetch("/score", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new ApiError(res.status, await ayikla(res));
  return (await res.json()) as ScoreResponse;
}

export async function postBatch(csv: string): Promise<BatchResponse> {
  const res = await fetch("/batch", {
    method: "POST",
    headers: { "content-type": "text/csv" },
    body: csv,
  });
  if (!res.ok) throw new ApiError(res.status, await ayikla(res));
  return (await res.json()) as BatchResponse;
}
