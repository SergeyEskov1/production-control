import pytest
from unittest.mock import AsyncMock, MagicMock
from src.domain.services.product_service import ProductService
from src.api.v1.schemas.product import ProductCreate

@pytest.fixture
def mock_product_repo():
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_by_code = AsyncMock()
    repo.aggregate = AsyncMock()
    return repo

@pytest.fixture
def mock_batch_repo():
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
def product_service(mock_product_repo, mock_batch_repo):
    return ProductService(mock_product_repo, mock_batch_repo)

class TestProductService:

    @pytest.mark.asyncio
    async def test_create_product_fails_for_closed_batch(
        self, product_service, mock_batch_repo
    ):
        mock_batch = MagicMock()
        mock_batch.is_closed = True
        mock_batch_repo.get_by_id.return_value = mock_batch

        with pytest.raises(ValueError, match="closed"):
            await product_service.create_product(
                ProductCreate(unique_code="CODE001", batch_id=1)
            )

    @pytest.mark.asyncio
    async def test_create_product_fails_for_nonexistent_batch(
        self, product_service, mock_batch_repo
    ):
        mock_batch_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await product_service.create_product(
                ProductCreate(unique_code="CODE001", batch_id=999)
            )

    @pytest.mark.asyncio
    async def test_aggregate_skips_already_aggregated(
        self, product_service, mock_batch_repo, mock_product_repo
    ):
        mock_batch = MagicMock()
        mock_batch.id = 1
        mock_batch_repo.get_by_id.return_value = mock_batch

        mock_product = MagicMock()
        mock_product.batch_id = 1
        mock_product.is_aggregated = True
        mock_product_repo.get_by_code.return_value = mock_product

        result = await product_service.aggregate_products(1, ["CODE001"])

        assert result["aggregated"] == 0
        assert result["failed"] == 1
        assert result["errors"][0]["reason"] == "already aggregated"
