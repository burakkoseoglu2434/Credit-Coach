from __future__ import annotations

try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Request
except Exception:  # pragma: no cover
    Depends = None
    FastAPI = None
    Header = None
    HTTPException = None
    Request = None

from credit_coach.api.auth import check_rate_limit, extract_bearer_token, has_required_scope, verify_token
from credit_coach.api.schemas import ScoreResponse


if FastAPI is not None:
    app = FastAPI(title="Credit Coach API", version="0.1.0")

    def _require_auth(  # type: ignore[misc]
        request: Request,  # noqa: ARG001
        authorization: str | None = Header(default=None),
    ):
        token = extract_bearer_token(authorization)
        if not verify_token(token):
            raise HTTPException(status_code=401, detail="Unauthorized")

        endpoint = request.url.path if request is not None else "/score/demo"
        if not has_required_scope(token, endpoint):
            raise HTTPException(status_code=403, detail="Forbidden")
        allowed, retry_after = check_rate_limit(token=token, endpoint=endpoint)
        if not allowed:
            headers = {}
            if retry_after is not None:
                headers["Retry-After"] = str(retry_after)
            raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=headers)
        return True

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/score/demo", response_model=ScoreResponse, dependencies=[Depends(_require_auth)])
    def score_demo():
        return ScoreResponse(pd=0.25, approve=True)
else:
    app = None
