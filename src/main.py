from fastapi import FastAPI
from src.api.v1.routers.batches import router as batches_router
from src.api.v1.routers.products import router as products_router
from src.api.v1.routers.tasks import router as tasks_router
from src.api.v1.routers.webhooks import router as webhooks_router
from src.api.v1.routers.analytics import router as analytics_router

app = FastAPI(
    title="Production Control API",
    description="API для управления производственными партиями",
    version="1.0.0",
)

app.include_router(batches_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    try:
        from src.storage.minio_service import minio_service
        minio_service.init_buckets()
        print("MinIO buckets initialized")
    except Exception as e:
        print(f"MinIO init error: {e}")


@app.get("/health")
async def health():
    return {"status": "ok"}
