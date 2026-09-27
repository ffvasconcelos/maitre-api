from fastapi import FastAPI
from sqlalchemy import text

from maitre_api.presentation.http.dependencies import DB_SESSION

app = FastAPI(
    title="Maitre API",
    version="0.1.0",
)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_check_db(session: DB_SESSION) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
