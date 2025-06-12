from datetime import datetime
from typing import Any, Optional, Type

from loguru import logger

from fides.api.api.deps import get_autoclose_db_session
from fides.api.schemas.external_storage import ExternalStorageMetadata
from fides.api.service.external_data_storage import (
    ExternalDataStorageError,
    ExternalDataStorageService,
)
from fides.api.util.data_size import LARGE_DATA_THRESHOLD_BYTES, calculate_data_size


class EncryptedLargeDataDescriptor:
    """
    A Python descriptor for database fields with encrypted external storage fallback.

    See the original implementation for detailed docstrings.
    """

    def __init__(
        self,
        field_name: str,
        empty_default: Optional[Any] = None,
        threshold_bytes: Optional[int] = None,
    ):
        self.field_name = field_name
        self.private_field = f"_{field_name}"
        self.empty_default = empty_default if empty_default is not None else []
        self.threshold_bytes = threshold_bytes or LARGE_DATA_THRESHOLD_BYTES
        self.model_class: Optional[str] = None
        self.name: Optional[str] = None

    # Descriptor protocol helpers

    def __set_name__(
        self, owner: Type, name: str
    ) -> None:  # noqa: D401 (docstring in orig file)
        self.name = name
        self.model_class = owner.__name__

    def _generate_storage_path(self, instance: Any) -> str:
        instance_id = getattr(instance, "id", None)
        if not instance_id:
            raise ValueError(f"Instance {instance} must have an 'id' attribute")
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")
        return f"{self.model_class}/{instance_id}/{self.field_name}/{timestamp}.txt"

    def __get__(self, instance: Any, owner: Type) -> Any:  # noqa: D401
        if instance is None:
            return self
        raw_data = getattr(instance, self.private_field)
        if raw_data is None:
            return None
        if isinstance(raw_data, dict) and "storage_type" in raw_data:
            logger.info(
                f"Reading {self.model_class}.{self.field_name} from external storage "
                f"({raw_data.get('storage_type')})"
            )
            try:
                metadata = ExternalStorageMetadata.model_validate(raw_data)
                data = self._retrieve_external_data(metadata)
                record_count = len(data) if isinstance(data, list) else "N/A"
                logger.info(
                    f"Successfully retrieved {self.model_class}.{self.field_name} "
                    f"from external storage (records: {record_count})"
                )
                return data if data is not None else self.empty_default
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    f"Failed to retrieve {self.model_class}.{self.field_name} "
                    f"from external storage: {str(e)}"
                )
                raise ExternalDataStorageError(
                    f"Failed to retrieve {self.field_name}: {str(e)}"
                ) from e
        else:
            return raw_data

    def __set__(self, instance: Any, value: Any) -> None:  # noqa: D401
        if not value:
            self._cleanup_external_data(instance)
            setattr(instance, self.private_field, self.empty_default)
            return
        try:
            current_data = self.__get__(instance, type(instance))
            if current_data == value:
                return
        except Exception:  # pylint: disable=broad-except
            pass

        data_size = calculate_data_size(value)
        if data_size > self.threshold_bytes:
            logger.info(
                f"{self.model_class}.{self.field_name}: Data size ({data_size:,} bytes) "
                f"exceeds threshold ({self.threshold_bytes:,} bytes), storing externally"
            )
            self._cleanup_external_data(instance)
            metadata = self._store_external_data(instance, value)
            setattr(instance, self.private_field, metadata.model_dump())
        else:
            self._cleanup_external_data(instance)
            setattr(instance, self.private_field, value)

    # External storage helpers

    def _store_external_data(self, instance: Any, data: Any) -> ExternalStorageMetadata:
        storage_path = self._generate_storage_path(instance)
        with get_autoclose_db_session() as session:
            metadata = ExternalDataStorageService.store_data(
                db=session,
                storage_path=storage_path,
                data=data,
            )
            logger.info(
                f"Stored {self.model_class}.{self.field_name} to external storage: {storage_path}"
            )
            return metadata

    @staticmethod
    def _retrieve_external_data(metadata: ExternalStorageMetadata) -> Any:  # noqa: D401
        with get_autoclose_db_session() as session:
            return ExternalDataStorageService.retrieve_data(
                db=session,
                metadata=metadata,
            )

    def _cleanup_external_data(self, instance: Any) -> None:  # noqa: D401
        raw_data = getattr(instance, self.private_field, None)
        if isinstance(raw_data, dict) and "storage_type" in raw_data:
            try:
                metadata = ExternalStorageMetadata.model_validate(raw_data)
                with get_autoclose_db_session() as session:
                    ExternalDataStorageService.delete_data(
                        db=session,
                        metadata=metadata,
                    )
                logger.info(
                    f"Cleaned up external storage for {self.model_class}.{self.field_name}: "
                    f"{metadata.file_key}"
                )
            except Exception as e:  # pylint: disable=broad-except
                logger.warning(
                    f"Failed to cleanup external {self.field_name}: {str(e)}"
                )

    # Public helper

    def cleanup(self, instance: Any) -> None:  # noqa: D401
        self._cleanup_external_data(instance)
