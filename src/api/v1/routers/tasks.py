from fastapi import APIRouter
from celery.result import AsyncResult
from src.celery_app import app as celery_app
from pydantic import BaseModel

router = APIRouter(prefix="/tasks", tags=["Задачи"])


class AggregateAsyncRequest(BaseModel):
    unique_codes: list[str]


class ReportRequest(BaseModel):
    format: str = "excel"
    email: str = None


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    response = {"task_id": task_id, "status": result.state}
    if result.state == "PROGRESS":
        response["result"] = result.info
    elif result.state == "SUCCESS":
        response["result"] = result.result
    elif result.state == "FAILURE":
        response["error"] = str(result.result)
    return response


@router.post("/batches/{batch_id}/aggregate-async", status_code=202)
async def aggregate_async(batch_id: int, data: AggregateAsyncRequest):
    from src.tasks.aggregation import aggregate_products_batch
    task = aggregate_products_batch.delay(
        batch_id=batch_id,
        unique_codes=data.unique_codes,
    )
    return {"task_id": task.id, "status": "PENDING", "message": "Aggregation task started"}


@router.post("/batches/{batch_id}/reports", status_code=202)
async def create_report(batch_id: int, data: ReportRequest):
    from src.tasks.reports import generate_batch_report
    task = generate_batch_report.delay(
        batch_id=batch_id,
        format=data.format,
        user_email=data.email,
    )
    return {"task_id": task.id, "status": "PENDING"}
