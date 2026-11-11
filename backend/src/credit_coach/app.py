from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from credit_coach.ayarlar import require_decision_log_off
from credit_coach.schemas import BatchResponse, HealthResponse, ScoreRequest, ScoreResponse
from credit_coach.scoring_service import GirdiHatasi, Kayit, Servis, parse_csv

VERSION = "0.1.0"
MAX_BODY_BYTES = 16 * 1024 * 1024


@asynccontextmanager
async def lifespan(_app: FastAPI):
    require_decision_log_off()
    yield


app = FastAPI(title="Credit Coach", version=VERSION, lifespan=lifespan)


@lru_cache(maxsize=1)
def get_servis() -> Servis:
    return Servis.varsayilan()


ServisDep = Annotated[Servis, Depends(get_servis)]


class GirdiHatasiYaniti(BaseModel):
    detail: list[str]


@app.exception_handler(GirdiHatasi)
async def girdi_hatasi(_request: Request, exc: GirdiHatasi) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.errors[:50]})


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 without echoing the input (NaN/Infinity in it would otherwise break the JSON body)."""
    detail = [
        {"loc": list(e["loc"]), "msg": str(e["msg"]), "type": str(e["type"])} for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detail})


@app.get("/health", response_model=HealthResponse, operation_id="getHealth")
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=VERSION)


@app.post("/score", response_model=ScoreResponse, operation_id="postScore")
def score(req: ScoreRequest, servis: ServisDep) -> ScoreResponse:
    """Support check, model, calibrator, decision (policy v1), recourse. Invalid input is 422."""
    return servis.score(Kayit(req.basvuru.model_dump(), req.basvuru_tarihi))


@app.post(
    "/batch",
    response_model=BatchResponse,
    operation_id="postBatch",
    responses={422: {"model": GirdiHatasiYaniti, "description": "Invalid CSV (no partial result)"}},
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"text/csv": {"schema": {"type": "string", "format": "binary"}}},
        }
    },
)
async def batch(request: Request, servis: ServisDep) -> BatchResponse:
    """CSV (at most 10,000 rows): header = allowed features + basvuru_tarihi (+ kayit_id)."""
    ctype = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if ctype not in {"text/csv", "text/plain"}:
        raise HTTPException(status_code=415, detail="content-type must be text/csv")
    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="body too large")
    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise GirdiHatasi(["dosya UTF-8 değil"]) from e
    kayitlar = await run_in_threadpool(parse_csv, text)
    return await run_in_threadpool(servis.batch, kayitlar)
