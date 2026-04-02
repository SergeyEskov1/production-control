import os
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from src.core.config import settings

# Названия бакетов — папки в MinIO
# reports = сгенерированные отчёты
# exports = экспортированные данные
# imports = загруженные файлы для импорта
BUCKETS = ["reports", "exports", "imports"]


class MinIOService:
    def __init__(self):
        # Создаём клиент MinIO
        # endpoint без http:// — клиент сам добавит схему
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def init_buckets(self):
        """Создать бакеты если не существуют.
        Вызывается при старте приложения."""
        for bucket in BUCKETS:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                print(f"Created bucket: {bucket}")

    def upload_file(
        self,
        bucket: str,
        file_path: str,
        object_name: str = None,
        expires_days: int = 7,
    ) -> str:
        """Загрузить файл в MinIO и вернуть presigned URL.
        
        Presigned URL — временная ссылка для скачивания файла.
        Не требует авторизации — можно отдать любому пользователю.
        Истекает через expires_days дней."""
        
        if object_name is None:
            object_name = os.path.basename(file_path)

        # Определяем тип файла по расширению
        content_type = self._get_content_type(file_path)

        # Загружаем файл в MinIO
        self.client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
            content_type=content_type,
        )

        # Генерируем временную ссылку для скачивания
        url = self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(days=expires_days),
        )

        return url

    def download_file(self, bucket: str, object_name: str, file_path: str):
        """Скачать файл из MinIO на диск."""
        self.client.fget_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
        )

    def delete_file(self, bucket: str, object_name: str):
        """Удалить файл из MinIO."""
        try:
            self.client.remove_object(bucket, object_name)
        except S3Error:
            pass

    def list_files(self, bucket: str, prefix: str = None):
        """Список файлов в бакете."""
        return list(self.client.list_objects(
            bucket_name=bucket,
            prefix=prefix,
            recursive=True,
        ))

    def _get_content_type(self, file_path: str) -> str:
        """Определить Content-Type по расширению файла."""
        ext = os.path.splitext(file_path)[1].lower()
        types = {
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".csv": "text/csv",
            ".pdf": "application/pdf",
            ".json": "application/json",
        }
        return types.get(ext, "application/octet-stream")


# Единственный экземпляр сервиса на всё приложение
minio_service = MinIOService()
