from fastapi import FastAPI

from credit_coach.schemas import HealthResponse

VERSION = "0.1.0"

app = FastAPI(title="Credit Coach", version=VERSION)


@app.get("/health", response_model=HealthResponse, operation_id="getHealth")
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=VERSION)
