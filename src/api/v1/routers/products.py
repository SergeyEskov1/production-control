from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.api.v1.schemas.product import ProductCreate, ProductResponse, AggregateRequest
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository
from src.domain.services.product_service import ProductService

router = APIRouter(tags=["Продукция"])


def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    product_repo = ProductRepository(db)
    batch_repo = BatchRepository(db)
    return ProductService(product_repo, batch_repo)


@router.post("/products", status_code=201, response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    """Добавить продукцию в партию"""
    try:
        return await service.create_product(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/aggregate")
async def aggregate_products(
    batch_id: int,
    data: AggregateRequest,
    service: ProductService = Depends(get_product_service),
):
    """Агрегировать продукцию — отметить как учтённую"""
    try:
        return await service.aggregate_products(batch_id, data.unique_codes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
