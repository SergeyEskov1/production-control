import pytest

BATCH_DATA = {
    "СтатусЗакрытия": False,
    "ПредставлениеЗаданияНаСмену": "Тестовое задание",
    "РабочийЦентр": "Цех №1",
    "Смена": "1 смена",
    "Бригада": "Бригада Иванова",
    "НомерПартии": 99999,
    "ДатаПартии": "2024-01-30",
    "Номенклатура": "Болт М10",
    "КодЕКН": "EKN-001",
    "ИдентификаторРЦ": "RC-TEST",
    "ДатаВремяНачалаСмены": "2024-01-30T08:00:00",
    "ДатаВремяОкончанияСмены": "2024-01-30T20:00:00",
}

class TestBatchesAPI:

    @pytest.mark.asyncio
    async def test_create_batch(self, client):
        response = await client.post("/api/v1/batches", json=[BATCH_DATA])
        assert response.status_code == 201
        data = response.json()
        assert data[0]["batch_number"] == 99999
        assert data[0]["is_closed"] == False

    @pytest.mark.asyncio
    async def test_get_batches_list(self, client):
        await client.post("/api/v1/batches", json=[BATCH_DATA])
        response = await client.get("/api/v1/batches")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_batch_not_found(self, client):
        response = await client.get("/api/v1/batches/9999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_batch_close(self, client):
        create_response = await client.post("/api/v1/batches", json=[BATCH_DATA])
        batch_id = create_response.json()[0]["id"]
        response = await client.patch(
            f"/api/v1/batches/{batch_id}",
            json={"is_closed": True}
        )
        assert response.status_code == 200
        assert response.json()["is_closed"] == True
        assert response.json()["closed_at"] is not None
