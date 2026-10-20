from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text

from maitre_api.presentation.http.dependencies import DBSession
from maitre_api.presentation.http.routers import orders, products, tables

app = FastAPI(
    title="Maitre API",
    version="0.1.0",
)

app.include_router(products.router)
app.include_router(tables.router)
app.include_router(orders.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_check_db(session: DBSession) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        ) from e
