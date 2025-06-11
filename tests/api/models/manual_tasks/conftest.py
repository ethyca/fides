from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskParentEntityType,
    ManualTaskType,
)


@pytest.fixture
def manual_task(
    db: Session, connection_config: ConnectionConfig
) -> Generator[ManualTask, None, None]:
    """Create a test manual task."""
    task = ManualTask.create(
        db=db,
        data={
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": f"{connection_config.id}_task",
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )
    yield task
    try:
        task.delete(db)
    except Exception as e:
        pass
