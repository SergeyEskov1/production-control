import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from src.domain.services.batch_service import BatchService
from src.api.v1.schemas.batch import BatchCreate, BatchUpdate

@pytest.fixture
def mock_repository():
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_list = AsyncMock()
    repo.update = AsyncMock()
    repo.get_work_center_by_identifier = AsyncMock()
    repo.create_work_center = AsyncMock()
    return repo

@pytest.fixture
def batch_service(mock_repository):
    return BatchService(mock_repository)

@pytest.fixture
def batch_create_data():
    return BatchCreate(**{
        "СтатусЗакрытия": False,
        "ПредставлениеЗаданияНаСмену": "Тестовое задание",
        "РабочийЦентр": "Цех №1",
        "Смена": "1 смена",
        "Бригада": "Бригада Иванова",
        "НомерПартии": 12345,
        "ДатаПартии": "2024-01-30",
        "Номенклатура": "Болт М10",
        "КодЕКН": "EKN-001",
        "ИдентификаторРЦ": "RC-001",
        "ДатаВремяНачалаСмены": "2024-01-30T08:00:00",
        "ДатаВремяОкончанияСмены": "2024-01-30T20:00:00",
    })

class TestBatchService:

    @pytest.mark.asyncio
    async def test_create_batch_creates_work_center_if_not_exists(
        self, batch_service, mock_repository, batch_create_data
    ):
        mock_repository.get_work_center_by_identifier.return_value = None
        mock_work_center = MagicMock()
        mock_work_center.id = 1
        mock_repository.create_work_center.return_value = mock_work_center
        mock_batch = MagicMock()
        mock_batch.products = []
        mock_repository.create.return_value = mock_batch

        result = await batch_service.create_batches([batch_create_data])

        mock_repository.create_work_center.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_batch_reuses_existing_work_center(
        self, batch_service, mock_repository, batch_create_data
    ):
        mock_work_center = MagicMock()
        mock_work_center.id = 1
        mock_repository.get_work_center_by_identifier.return_value = mock_work_center
        mock_batch = MagicMock()
        mock_batch.products = []
        mock_repository.create.return_value = mock_batch

        await batch_service.create_batches([batch_create_data])

        mock_repository.create_work_center.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_batch_sets_closed_at_when_closing(
        self, batch_service, mock_repository
    ):
        mock_batch = MagicMock()
        mock_batch.is_closed = False
        mock_batch.closed_at = None
        mock_batch.products = []
        mock_repository.get_by_id.return_value = mock_batch
        mock_repository.update.return_value = mock_batch

        await batch_service.update_batch(1, BatchUpdate(is_closed=True))

        assert mock_batch.closed_at is not None
        assert mock_batch.is_closed == True

    @pytest.mark.asyncio
    async def test_get_batch_returns_none_for_nonexistent(
        self, batch_service, mock_repository
    ):
        mock_repository.get_by_id.return_value = None
        result = await batch_service.get_batch(999)
        assert result is None
