# Purpose-Based Data Model Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Phase 1 of the purpose-based data model: new tables, models, CRUD services, and API routes for Data Purpose, Data Consumer, Data Producer, and dataset purpose assignment.

**Architecture:** Models and migrations in fides OSS, services and routes in fidesplus. DataConsumer uses a facade pattern: system-type consumers are read from `ctl_systems` + `system_purpose` join table; non-system consumers (group/project) use a new `data_consumer` table. All dataset purposes are soft `fides_key` string references.

**Tech Stack:** Python 3, SQLAlchemy, Alembic, FastAPI, Pydantic v2, PostgreSQL, pytest

**Spec:** `docs/superpowers/specs/2026-03-11-purpose-based-data-model-design.md`

---

## File Structure

### fides OSS (models, migrations, schemas, scopes)

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `src/fides/api/models/data_purpose.py` | DataPurpose model |
| Modify | `src/fides/api/models/sql_models.py` | Add Dataset columns, add System relationship |
| Create | `src/fides/api/models/data_consumer.py` | DataConsumer model, DataConsumerPurpose join table |
| Create | `src/fides/api/models/system_purpose.py` | SystemPurpose join table |
| Create | `src/fides/api/models/data_producer.py` | DataProducer model, DataProducerMember join table |
| Create | `src/fides/api/schemas/data_purpose.py` | DataPurpose Pydantic schemas (create, update, response) |
| Create | `src/fides/api/schemas/data_consumer.py` | DataConsumer Pydantic schemas |
| Create | `src/fides/api/schemas/data_producer.py` | DataProducer Pydantic schemas |
| Modify | `src/fides/api/db/base.py` | Import new models so Alembic sees them |
| Create | `src/fides/api/alembic/migrations/versions/xx_..._purpose_based_data_model.py` | Migration for all new tables + dataset columns |

### fidesplus (services, routes, settings)

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `src/fidesplus/config/purpose_settings.py` | Feature flag settings class |
| Modify | `src/fidesplus/config/__init__.py` | Register PurposeSettings on FidesplusConfig |
| Create | `src/fidesplus/service/data_purpose/__init__.py` | Package init |
| Create | `src/fidesplus/service/data_purpose/data_purpose_service.py` | DataPurpose CRUD + validation |
| Create | `src/fidesplus/service/data_consumer/__init__.py` | Package init |
| Create | `src/fidesplus/service/data_consumer/data_consumer_service.py` | DataConsumer facade service |
| Create | `src/fidesplus/service/data_producer/__init__.py` | Package init |
| Create | `src/fidesplus/service/data_producer/data_producer_service.py` | DataProducer CRUD + member management |
| Create | `src/fidesplus/api/routes/data_purpose.py` | DataPurpose API routes |
| Create | `src/fidesplus/api/routes/data_consumer.py` | DataConsumer API routes + purpose assignment |
| Create | `src/fidesplus/api/routes/data_producer.py` | DataProducer API routes + member management |
| Modify | `src/fidesplus/api/plus_scope_registry.py` | Define scopes, add to SCOPE_DOCS and role mappings |
| Modify | `src/fidesplus/api/urn_registry.py` | Add URL path constants |
| Modify | `src/fidesplus/api/deps.py` | Add service factory functions for Depends() |
| Modify | Router registration file | Mount new routers on plus_router |

### Tests

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `tests/ops/models/test_data_purpose.py` | DataPurpose model unit tests |
| Create | `tests/ops/models/test_data_consumer.py` | DataConsumer + join table model tests |
| Create | `tests/ops/models/test_system_purpose.py` | SystemPurpose join table tests |
| Create | `tests/ops/models/test_data_producer.py` | DataProducer + member model tests |
| Create | `tests/ops/models/test_dataset_purposes.py` | Dataset purpose column + JSON validation |
| Create | (fidesplus) `tests/ops/api/test_data_purpose_api.py` | DataPurpose API endpoint tests |
| Create | (fidesplus) `tests/ops/api/test_data_consumer_api.py` | DataConsumer API endpoint tests |
| Create | (fidesplus) `tests/ops/api/test_data_producer_api.py` | DataProducer API endpoint tests |
| Create | (fidesplus) `tests/ops/service/test_data_purpose_service.py` | DataPurposeService integration tests |
| Create | (fidesplus) `tests/ops/service/test_data_consumer_service.py` | DataConsumerService facade tests |
| Create | (fidesplus) `tests/ops/service/test_data_producer_service.py` | DataProducerService integration tests |

---

## Chunk 1: Models and Migration (fides OSS)

### Task 1: DataPurpose Model

**Files:**
- Create: `src/fides/api/models/data_purpose.py`
- Test: `tests/ops/models/test_data_purpose.py`

- [ ] **Step 1: Write the model test**

```python
# tests/ops/models/test_data_purpose.py
import pytest
from sqlalchemy.orm import Session

from fides.api.models.data_purpose import DataPurpose


class TestDataPurposeModel:
    def test_create_data_purpose(self, db: Session):
        purpose = DataPurpose.create(
            db=db,
            data={
                "fides_key": "marketing_email",
                "name": "Email Marketing",
                "description": "Processing for email marketing campaigns",
                "data_use": "marketing.advertising",
                "data_subject": "customer",
                "data_categories": ["user.contact.email"],
                "legal_basis_for_processing": "Consent",
                "flexible_legal_basis_for_processing": True,
                "retention_period": "90 days",
                "features": ["email_targeting"],
            },
        )
        assert purpose.fides_key == "marketing_email"
        assert purpose.data_use == "marketing.advertising"
        assert purpose.data_subject == "customer"
        assert purpose.data_categories == ["user.contact.email"]
        assert purpose.flexible_legal_basis_for_processing is True
        assert purpose.features == ["email_targeting"]
        assert purpose.id is not None
        assert purpose.created_at is not None

    def test_create_minimal_data_purpose(self, db: Session):
        """Only fides_key, name, and data_use are required."""
        purpose = DataPurpose.create(
            db=db,
            data={
                "fides_key": "analytics_basic",
                "name": "Basic Analytics",
                "data_use": "analytics",
            },
        )
        assert purpose.fides_key == "analytics_basic"
        assert purpose.data_subject is None
        assert purpose.data_categories == []
        assert purpose.legal_basis_for_processing is None

    def test_fides_key_uniqueness(self, db: Session):
        DataPurpose.create(
            db=db,
            data={
                "fides_key": "unique_purpose",
                "name": "Purpose A",
                "data_use": "analytics",
            },
        )
        with pytest.raises(Exception):
            DataPurpose.create(
                db=db,
                data={
                    "fides_key": "unique_purpose",
                    "name": "Purpose B",
                    "data_use": "marketing",
                },
            )

    def test_delete_data_purpose(self, db: Session):
        purpose = DataPurpose.create(
            db=db,
            data={
                "fides_key": "to_delete",
                "name": "Delete Me",
                "data_use": "analytics",
            },
        )
        purpose_id = purpose.id
        purpose.delete(db)
        assert db.query(DataPurpose).filter_by(id=purpose_id).first() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_data_purpose.py -v`
Expected: ImportError (module does not exist yet)

- [ ] **Step 3: Write the DataPurpose model**

**Important:** `FidesBase` (the mixin providing `fides_key`, `name`, `description`, `organization_fides_key`, `tags`) is defined in `sql_models.py`, NOT in `base_class.py`. The `Base` class from `base_class.py` provides `id`, `created_at`, `updated_at`, and CRUD methods. Models inheriting both get a composite primary key (`id` + `fides_key`). This is the same pattern used by `System`, `Dataset`, `DataCategory`, etc. Join tables reference `data_purpose.id` (the UUID column), which works because `id` is part of the composite PK.

Create `src/fides/api/models/data_purpose.py`. Import `FidesBase` from `sql_models` and `Base` from `base_class`. There is no circular import since `sql_models.py` does not import from `data_purpose.py`.

```python
# src/fides/api/models/data_purpose.py
from typing import Any

from sqlalchemy import ARRAY, Boolean, Column, String
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base
from fides.api.models.sql_models import FidesBase


class DataPurpose(Base, FidesBase):
    """
    A standalone, reusable declaration of why data is processed.
    Replaces the system-bound PrivacyDeclaration with a centrally-governed entity.
    Flat (no hierarchy) but inherits FidesBase for fides_key, name, description,
    organization_fides_key, and tags.
    """

    __tablename__ = "data_purpose"

    data_use = Column(String, nullable=False, index=True)
    data_subject = Column(String, nullable=True)
    data_categories = Column(ARRAY(String), server_default="{}", nullable=False)
    legal_basis_for_processing = Column(String, nullable=True)
    flexible_legal_basis_for_processing = Column(
        Boolean, server_default="t", nullable=False
    )
    special_category_legal_basis = Column(String, nullable=True)
    impact_assessment_location = Column(String, nullable=True)
    retention_period = Column(String, nullable=True)
    features = Column(ARRAY(String), server_default="{}", nullable=False)

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> "DataPurpose":
        """Override create to skip name uniqueness check.
        DataPurpose uses fides_key for uniqueness, not name."""
        return super().create(db=db, data=data, check_name=check_name)
```

Columns inherited from `FidesBase` (do NOT redeclare): `fides_key`, `name`, `description`, `organization_fides_key`, `tags`.
Columns inherited from `Base` (do NOT redeclare): `id`, `created_at`, `updated_at`.

- [ ] **Step 4: Register model in base imports**

Add to `src/fides/api/db/base.py`:
```python
from fides.api.models.data_purpose import DataPurpose  # noqa: F401
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_data_purpose.py -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/fides/api/models/data_purpose.py src/fides/api/db/base.py tests/ops/models/test_data_purpose.py
git commit -m "feat: add DataPurpose model with unit tests"
```

---

### Task 2: SystemPurpose Join Table

**Files:**
- Create: `src/fides/api/models/system_purpose.py`
- Modify: `src/fides/api/models/sql_models.py` (add relationship to System)
- Test: `tests/ops/models/test_system_purpose.py`

- [ ] **Step 1: Write the test**

```python
# tests/ops/models/test_system_purpose.py
import pytest
from sqlalchemy.orm import Session

from fides.api.models.data_purpose import DataPurpose
from fides.api.models.system_purpose import SystemPurpose
from fides.api.models.sql_models import System


class TestSystemPurposeModel:
    @pytest.fixture
    def purpose(self, db: Session) -> DataPurpose:
        return DataPurpose.create(
            db=db,
            data={
                "fides_key": "test_purpose",
                "name": "Test Purpose",
                "data_use": "analytics",
            },
        )

    def test_create_system_purpose(self, db: Session, system: System, purpose: DataPurpose):
        sp = SystemPurpose.create(
            db=db,
            data={
                "system_id": system.id,
                "data_purpose_id": purpose.id,
            },
        )
        assert sp.system_id == system.id
        assert sp.data_purpose_id == purpose.id
        assert sp.assigned_by is None
        assert sp.created_at is not None

    def test_unique_constraint(self, db: Session, system: System, purpose: DataPurpose):
        SystemPurpose.create(
            db=db,
            data={
                "system_id": system.id,
                "data_purpose_id": purpose.id,
            },
        )
        with pytest.raises(Exception):
            SystemPurpose.create(
                db=db,
                data={
                    "system_id": system.id,
                    "data_purpose_id": purpose.id,
                },
            )

    def test_cascade_on_system_delete(self, db: Session, system: System, purpose: DataPurpose):
        sp = SystemPurpose.create(
            db=db,
            data={
                "system_id": system.id,
                "data_purpose_id": purpose.id,
            },
        )
        sp_id = sp.id
        system.delete(db)
        assert db.query(SystemPurpose).filter_by(id=sp_id).first() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_system_purpose.py -v`
Expected: ImportError

- [ ] **Step 3: Write the SystemPurpose model**

```python
# src/fides/api/models/system_purpose.py
from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base


class SystemPurpose(Base):
    """
    Audited join table linking a System to a DataPurpose.
    Used by the DataConsumer facade for system-type consumers.
    """

    __tablename__ = "system_purpose"
    __table_args__ = (
        UniqueConstraint("system_id", "data_purpose_id", name="uq_system_purpose"),
    )

    system_id = Column(
        String,
        ForeignKey("ctl_systems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_purpose_id = Column(
        String,
        ForeignKey("data_purpose.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_by = Column(
        String,
        ForeignKey("fidesuser.id"),
        nullable=True,
    )

    system = relationship("System", lazy="selectin")
    data_purpose = relationship("DataPurpose", lazy="selectin")
```

- [ ] **Step 4: Add `system_purposes` relationship to System model**

In `src/fides/api/models/sql_models.py`, add to the `System` class after the `system_groups` relationship:

```python
    system_purposes = relationship(
        "SystemPurpose",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
```

- [ ] **Step 5: Register model in base imports**

Add to `src/fides/api/db/base.py`:
```python
from fides.api.models.system_purpose import SystemPurpose  # noqa: F401
```

- [ ] **Step 6: Run tests**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_system_purpose.py -v`
Expected: All 3 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/fides/api/models/system_purpose.py src/fides/api/models/sql_models.py src/fides/api/db/base.py tests/ops/models/test_system_purpose.py
git commit -m "feat: add SystemPurpose join table with cascade delete"
```

---

### Task 3: DataConsumer Model and DataConsumerPurpose Join Table

**Files:**
- Create: `src/fides/api/models/data_consumer.py`
- Test: `tests/ops/models/test_data_consumer.py`

- [ ] **Step 1: Write the test**

```python
# tests/ops/models/test_data_consumer.py
import pytest
from sqlalchemy.orm import Session

from fides.api.models.data_consumer import DataConsumer, DataConsumerPurpose
from fides.api.models.data_purpose import DataPurpose


class TestDataConsumerModel:
    def test_create_group_consumer(self, db: Session):
        consumer = DataConsumer.create(
            db=db,
            data={
                "name": "Marketing Team",
                "description": "Marketing department Google Group",
                "type": "group",
                "external_id": "marketing@example.com",
                "contact_email": "marketing-lead@example.com",
                "tags": ["marketing", "internal"],
            },
        )
        assert consumer.name == "Marketing Team"
        assert consumer.type == "group"
        assert consumer.external_id == "marketing@example.com"
        assert consumer.tags == ["marketing", "internal"]

    def test_create_project_consumer(self, db: Session):
        consumer = DataConsumer.create(
            db=db,
            data={
                "name": "Analytics Pipeline",
                "type": "project",
                "external_id": "bigquery-project-123",
            },
        )
        assert consumer.type == "project"

    def test_system_type_rejected(self, db: Session):
        """CHECK constraint prevents type='system' rows."""
        with pytest.raises(Exception):
            DataConsumer.create(
                db=db,
                data={
                    "name": "Should Fail",
                    "type": "system",
                },
            )

    def test_custom_type_allowed(self, db: Session):
        consumer = DataConsumer.create(
            db=db,
            data={
                "name": "Custom Consumer",
                "type": "data_warehouse",
            },
        )
        assert consumer.type == "data_warehouse"


class TestDataConsumerPurposeModel:
    @pytest.fixture
    def purpose(self, db: Session) -> DataPurpose:
        return DataPurpose.create(
            db=db,
            data={
                "fides_key": "consumer_test_purpose",
                "name": "Test Purpose",
                "data_use": "analytics",
            },
        )

    @pytest.fixture
    def consumer(self, db: Session) -> DataConsumer:
        return DataConsumer.create(
            db=db,
            data={
                "name": "Test Group",
                "type": "group",
            },
        )

    def test_link_purpose_to_consumer(self, db: Session, consumer: DataConsumer, purpose: DataPurpose):
        link = DataConsumerPurpose.create(
            db=db,
            data={
                "data_consumer_id": consumer.id,
                "data_purpose_id": purpose.id,
            },
        )
        assert link.data_consumer_id == consumer.id
        assert link.data_purpose_id == purpose.id

    def test_unique_constraint(self, db: Session, consumer: DataConsumer, purpose: DataPurpose):
        DataConsumerPurpose.create(
            db=db,
            data={
                "data_consumer_id": consumer.id,
                "data_purpose_id": purpose.id,
            },
        )
        with pytest.raises(Exception):
            DataConsumerPurpose.create(
                db=db,
                data={
                    "data_consumer_id": consumer.id,
                    "data_purpose_id": purpose.id,
                },
            )

    def test_cascade_on_consumer_delete(self, db: Session, consumer: DataConsumer, purpose: DataPurpose):
        link = DataConsumerPurpose.create(
            db=db,
            data={
                "data_consumer_id": consumer.id,
                "data_purpose_id": purpose.id,
            },
        )
        link_id = link.id
        consumer.delete(db)
        assert db.query(DataConsumerPurpose).filter_by(id=link_id).first() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_data_consumer.py -v`
Expected: ImportError

- [ ] **Step 3: Write the DataConsumer and DataConsumerPurpose models**

```python
# src/fides/api/models/data_consumer.py
from typing import Any

from sqlalchemy import ARRAY, JSON, Boolean, CheckConstraint, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base


class DataConsumer(Base):
    """
    Non-system data consumers (groups, projects, custom types).
    System-type consumers are surfaced via a facade over ctl_systems.
    """

    __tablename__ = "data_consumer"
    __table_args__ = (
        CheckConstraint("type != 'system'", name="ck_data_consumer_not_system"),
    )

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False, index=True)
    external_id = Column(String, nullable=True)
    egress = Column(JSON, nullable=True)
    ingress = Column(JSON, nullable=True)
    data_shared_with_third_parties = Column(
        Boolean, server_default="f", nullable=False
    )
    third_parties = Column(String, nullable=True)
    shared_categories = Column(ARRAY(String), server_default="{}", nullable=False)
    contact_email = Column(String, nullable=True)
    contact_slack_channel = Column(String, nullable=True)
    contact_details = Column(JSON, nullable=True)
    tags = Column(ARRAY(String), server_default="{}", nullable=False)

    consumer_purposes = relationship(
        "DataConsumerPurpose",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> "DataConsumer":
        """Override create to skip name uniqueness check.
        Multiple consumers can share a name."""
        return super().create(db=db, data=data, check_name=check_name)


class DataConsumerPurpose(Base):
    """
    Audited join table linking a non-system DataConsumer to a DataPurpose.
    """

    __tablename__ = "data_consumer_purpose"
    __table_args__ = (
        UniqueConstraint(
            "data_consumer_id", "data_purpose_id", name="uq_data_consumer_purpose"
        ),
    )

    data_consumer_id = Column(
        String,
        ForeignKey("data_consumer.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_purpose_id = Column(
        String,
        ForeignKey("data_purpose.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_by = Column(
        String,
        ForeignKey("fidesuser.id"),
        nullable=True,
    )

    data_consumer = relationship("DataConsumer", lazy="selectin")
    data_purpose = relationship("DataPurpose", lazy="selectin")
```

- [ ] **Step 4: Register models in base imports**

Add to `src/fides/api/db/base.py`:
```python
from fides.api.models.data_consumer import DataConsumer, DataConsumerPurpose  # noqa: F401
```

- [ ] **Step 5: Run tests**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_data_consumer.py -v`
Expected: All 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/fides/api/models/data_consumer.py src/fides/api/db/base.py tests/ops/models/test_data_consumer.py
git commit -m "feat: add DataConsumer and DataConsumerPurpose models"
```

---

### Task 4: DataProducer Model and DataProducerMember Join Table

**Files:**
- Create: `src/fides/api/models/data_producer.py`
- Test: `tests/ops/models/test_data_producer.py`

- [ ] **Step 1: Write the test**

```python
# tests/ops/models/test_data_producer.py
import pytest
from sqlalchemy.orm import Session

from fides.api.models.data_producer import DataProducer, DataProducerMember


class TestDataProducerModel:
    def test_create_data_producer(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={
                "name": "Analytics Engineering Team",
                "description": "Responsible for analytics pipelines",
                "external_id": "analytics-eng-okta-group",
                "contact_email": "analytics-eng@example.com",
                "contact_slack_channel": "#analytics-eng",
            },
        )
        assert producer.name == "Analytics Engineering Team"
        assert producer.external_id == "analytics-eng-okta-group"
        assert producer.contact_email == "analytics-eng@example.com"

    def test_create_minimal_producer(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={"name": "Minimal Producer"},
        )
        assert producer.name == "Minimal Producer"
        assert producer.monitor_id is None

    def test_delete_producer(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={"name": "Delete Me"},
        )
        producer_id = producer.id
        producer.delete(db)
        assert db.query(DataProducer).filter_by(id=producer_id).first() is None


class TestDataProducerMemberModel:
    @pytest.fixture
    def producer(self, db: Session) -> DataProducer:
        return DataProducer.create(
            db=db,
            data={"name": "Test Producer"},
        )

    def test_add_member(self, db: Session, producer: DataProducer, user):
        member = DataProducerMember.create(
            db=db,
            data={
                "data_producer_id": producer.id,
                "user_id": user.id,
            },
        )
        assert member.data_producer_id == producer.id
        assert member.user_id == user.id

    def test_unique_constraint(self, db: Session, producer: DataProducer, user):
        DataProducerMember.create(
            db=db,
            data={
                "data_producer_id": producer.id,
                "user_id": user.id,
            },
        )
        with pytest.raises(Exception):
            DataProducerMember.create(
                db=db,
                data={
                    "data_producer_id": producer.id,
                    "user_id": user.id,
                },
            )

    def test_cascade_on_producer_delete(self, db: Session, producer: DataProducer, user):
        member = DataProducerMember.create(
            db=db,
            data={
                "data_producer_id": producer.id,
                "user_id": user.id,
            },
        )
        member_id = member.id
        producer.delete(db)
        assert db.query(DataProducerMember).filter_by(id=member_id).first() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_data_producer.py -v`
Expected: ImportError

- [ ] **Step 3: Write the DataProducer and DataProducerMember models**

```python
# src/fides/api/models/data_producer.py
from typing import Any

from sqlalchemy import JSON, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base


class DataProducer(Base):
    """
    Represents a team or group responsible for data registration
    and purpose assignment to datasets.
    """

    __tablename__ = "data_producer"

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    external_id = Column(String, nullable=True)
    monitor_id = Column(
        String,
        ForeignKey("monitorconfig.id"),
        nullable=True,
    )
    contact_email = Column(String, nullable=True)
    contact_slack_channel = Column(String, nullable=True)
    contact_details = Column(JSON, nullable=True)

    members = relationship(
        "DataProducerMember",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    monitor = relationship("MonitorConfig", lazy="selectin")

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> "DataProducer":
        """Override create to skip name uniqueness check.
        Multiple producers can share a name."""
        return super().create(db=db, data=data, check_name=check_name)


class DataProducerMember(Base):
    """
    Join table linking a DataProducer to FidesUser members.
    """

    __tablename__ = "data_producer_member"
    __table_args__ = (
        UniqueConstraint(
            "data_producer_id", "user_id", name="uq_data_producer_member"
        ),
    )

    data_producer_id = Column(
        String,
        ForeignKey("data_producer.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String,
        ForeignKey("fidesuser.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    data_producer = relationship("DataProducer", lazy="selectin")
    user = relationship("FidesUser", lazy="selectin")
```

- [ ] **Step 4: Register models in base imports**

Add to `src/fides/api/db/base.py`:
```python
from fides.api.models.data_producer import DataProducer, DataProducerMember  # noqa: F401
```

- [ ] **Step 5: Run tests**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_data_producer.py -v`
Expected: All 6 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/fides/api/models/data_producer.py src/fides/api/db/base.py tests/ops/models/test_data_producer.py
git commit -m "feat: add DataProducer and DataProducerMember models"
```

---

### Task 5: Extend Dataset Model

**Files:**
- Modify: `src/fides/api/models/sql_models.py` (add columns to Dataset)
- Test: `tests/ops/models/test_dataset_purposes.py`

- [ ] **Step 1: Write the test**

```python
# tests/ops/models/test_dataset_purposes.py
import pytest
from sqlalchemy.orm import Session

from fides.api.models.sql_models import Dataset
from fides.api.models.data_purpose import DataPurpose
from fides.api.models.data_producer import DataProducer


class TestDatasetPurposes:
    def test_dataset_with_purposes(self, db: Session):
        dataset = Dataset.create(
            db=db,
            data={
                "fides_key": "test_dataset_purposes",
                "name": "Test Dataset",
                "data_categories": [],
                "collections": [],
                "data_purposes": ["marketing_email", "analytics_basic"],
            },
        )
        assert dataset.data_purposes == ["marketing_email", "analytics_basic"]

    def test_dataset_without_purposes(self, db: Session):
        dataset = Dataset.create(
            db=db,
            data={
                "fides_key": "test_dataset_no_purposes",
                "name": "Test Dataset No Purposes",
                "data_categories": [],
                "collections": [],
            },
        )
        assert dataset.data_purposes == [] or dataset.data_purposes is None

    def test_dataset_with_producer(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={"name": "Test Producer"},
        )
        dataset = Dataset.create(
            db=db,
            data={
                "fides_key": "test_dataset_producer",
                "name": "Test Dataset With Producer",
                "data_categories": [],
                "collections": [],
                "data_producer_id": producer.id,
            },
        )
        assert dataset.data_producer_id == producer.id

    def test_producer_set_null_on_delete(self, db: Session):
        producer = DataProducer.create(
            db=db,
            data={"name": "Delete Producer"},
        )
        dataset = Dataset.create(
            db=db,
            data={
                "fides_key": "test_dataset_producer_delete",
                "name": "Test Dataset",
                "data_categories": [],
                "collections": [],
                "data_producer_id": producer.id,
            },
        )
        dataset_id = dataset.id
        producer.delete(db)
        db.expire_all()
        refreshed = db.query(Dataset).filter_by(id=dataset_id).first()
        assert refreshed.data_producer_id is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_dataset_purposes.py -v`
Expected: FAIL (columns don't exist yet)

- [ ] **Step 3: Add columns to Dataset model**

In `src/fides/api/models/sql_models.py`, add to the `Dataset` class after `fides_meta`:

```python
    data_purposes = Column(ARRAY(String), server_default="{}", nullable=True)
    data_producer_id = Column(
        String,
        ForeignKey("data_producer.id", ondelete="SET NULL"),
        nullable=True,
    )
    data_producer = relationship("DataProducer", lazy="selectin")
```

- [ ] **Step 4: Run tests**

Run: `nox -s "pytest(ops-unit)" -- tests/ops/models/test_dataset_purposes.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/fides/api/models/sql_models.py tests/ops/models/test_dataset_purposes.py
git commit -m "feat: add data_purposes and data_producer_id to Dataset model"
```

---

### Task 6: Permission Scopes

**Note:** Since the purpose-based data model is a fidesplus-only feature, scope constants follow the established pattern of being defined in `plus_scope_registry.py` (not OSS `scope_registry.py`). This is consistent with how `SYSTEM_GROUP`, `DISCOVERY_MONITOR`, `TAXONOMY`, and other fidesplus feature scopes are defined. The scope definitions, `UPDATED_SCOPE_DOCS` entries, and role mappings are all handled in Task 13. **This task is a no-op and is merged into Task 13.**

Skip to Task 7.

---

### Task 7: Alembic Migration

**Files:**
- Create: `src/fides/api/alembic/migrations/versions/xx_..._purpose_based_data_model.py`

- [ ] **Step 1: Auto-generate migration**

```bash
cd /Users/adriangalvan/Documents/Github/fides
nox -s generate_migration -- "purpose_based_data_model"
```

If `nox -s generate_migration` is not available, manually create the migration:

```bash
cd src/fides/api
alembic revision --autogenerate -m "purpose_based_data_model"
```

- [ ] **Step 2: Review and edit the generated migration**

Verify the generated migration includes:
1. `data_purpose` table creation
2. `data_consumer` table creation with CHECK constraint
3. `data_consumer_purpose` join table
4. `system_purpose` join table
5. `data_producer` table
6. `data_producer_member` join table
7. ALTER `ctl_datasets` to add `data_purposes` and `data_producer_id` columns

Ensure all indexes are present per the spec. Add any missing CHECK constraints or cascade behaviors manually.

- [ ] **Step 3: Test the migration**

```bash
nox -s check_migrations
```

Expected: Migration check passes

- [ ] **Step 4: Commit**

```bash
git add src/fides/api/alembic/migrations/versions/
git commit -m "feat: add alembic migration for purpose-based data model tables"
```

---

### Task 8: Pydantic Schemas

**Files:**
- Create: `src/fides/api/schemas/data_purpose.py`
- Create: `src/fides/api/schemas/data_consumer.py`
- Create: `src/fides/api/schemas/data_producer.py`

- [ ] **Step 1: Write DataPurpose schemas**

```python
# src/fides/api/schemas/data_purpose.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DataPurposeCreate(BaseModel):
    fides_key: str
    name: str
    description: Optional[str] = None
    organization_fides_key: Optional[str] = "default_organization"
    tags: Optional[List[str]] = None
    data_use: str
    data_subject: Optional[str] = None
    data_categories: List[str] = Field(default_factory=list)
    legal_basis_for_processing: Optional[str] = None
    flexible_legal_basis_for_processing: bool = True
    special_category_legal_basis: Optional[str] = None
    impact_assessment_location: Optional[str] = None
    retention_period: Optional[str] = None
    features: List[str] = Field(default_factory=list)


class DataPurposeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data_use: Optional[str] = None
    data_subject: Optional[str] = None
    data_categories: Optional[List[str]] = None
    legal_basis_for_processing: Optional[str] = None
    flexible_legal_basis_for_processing: Optional[bool] = None
    special_category_legal_basis: Optional[str] = None
    impact_assessment_location: Optional[str] = None
    retention_period: Optional[str] = None
    features: Optional[List[str]] = None


class DataPurposeResponse(BaseModel):
    id: str
    fides_key: str
    name: str
    description: Optional[str] = None
    organization_fides_key: Optional[str] = None
    tags: Optional[List[str]] = None
    data_use: str
    data_subject: Optional[str] = None
    data_categories: List[str]
    legal_basis_for_processing: Optional[str] = None
    flexible_legal_basis_for_processing: bool
    special_category_legal_basis: Optional[str] = None
    impact_assessment_location: Optional[str] = None
    retention_period: Optional[str] = None
    features: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Write DataConsumer schemas**

```python
# src/fides/api/schemas/data_consumer.py
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from fides.api.schemas.data_purpose import DataPurposeResponse


class DataConsumerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    external_id: Optional[str] = None
    egress: Optional[Dict] = None
    ingress: Optional[Dict] = None
    data_shared_with_third_parties: bool = False
    third_parties: Optional[str] = None
    shared_categories: List[str] = Field(default_factory=list)
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None
    tags: List[str] = Field(default_factory=list)


class DataConsumerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    egress: Optional[Dict] = None
    ingress: Optional[Dict] = None
    data_shared_with_third_parties: Optional[bool] = None
    third_parties: Optional[str] = None
    shared_categories: Optional[List[str]] = None
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None
    tags: Optional[List[str]] = None


class DataConsumerPurposeAssignment(BaseModel):
    purpose_fides_keys: List[str]


class DataConsumerResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    type: str
    external_id: Optional[str] = None
    purposes: List[DataPurposeResponse] = Field(default_factory=list)
    system_fides_key: Optional[str] = None
    vendor_id: Optional[str] = None
    egress: Optional[Dict] = None
    ingress: Optional[Dict] = None
    data_shared_with_third_parties: Optional[bool] = None
    third_parties: Optional[str] = None
    shared_categories: Optional[List[str]] = None
    tags: List[str] = Field(default_factory=list)
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 3: Write DataProducer schemas**

```python
# src/fides/api/schemas/data_producer.py
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DataProducerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    external_id: Optional[str] = None
    monitor_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None


class DataProducerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    monitor_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None


class DataProducerMemberAssignment(BaseModel):
    user_ids: List[str]


class DataProducerResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    external_id: Optional[str] = None
    monitor_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None
    member_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 4: Extend Dataset response schema**

The Dataset schema comes from the `fideslang` library. To surface `data_purposes` and `data_producer_id` in API responses, create a response schema extension. Find the existing Dataset response schema in fides (likely in `src/fides/api/schemas/dataset.py` or similar) and extend it:

```python
# Add to the existing dataset schema file or create src/fides/api/schemas/dataset_extensions.py
from typing import List, Optional

from pydantic import Field


class DatasetPurposesMixin:
    """Mixin to add purpose-based fields to dataset responses."""
    data_purposes: List[str] = Field(default_factory=list)
    data_producer_id: Optional[str] = None
```

If the existing dataset response schema is a fideslang model used directly, create a wrapper:

```python
class DatasetResponseWithPurposes(FideslangDatasetResponse):
    data_purposes: List[str] = Field(default_factory=list)
    data_producer_id: Optional[str] = None
```

The exact approach depends on how the existing dataset GET endpoint constructs its response. The implementer should trace the existing dataset GET handler to determine the right extension point.

- [ ] **Step 5: Commit**

```bash
git add src/fides/api/schemas/data_purpose.py src/fides/api/schemas/data_consumer.py src/fides/api/schemas/data_producer.py
git commit -m "feat: add Pydantic schemas for data purpose, consumer, producer"
```

---

## Chunk 2: Services (fidesplus)

### Task 9: Feature Flag and Settings

**Files:**
- Create: `src/fidesplus/config/purpose_settings.py`
- Modify: `src/fidesplus/config/__init__.py` (add to FidesplusConfig)

- [ ] **Step 1: Create the settings class**

```python
# src/fidesplus/config/purpose_settings.py
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from fidesplus.config.fidesplus_settings import FidesplusSettings


class PurposeSettings(FidesplusSettings):
    """Settings for the purpose-based data model feature."""

    model_config = SettingsConfigDict(env_prefix="FIDESPLUS__PURPOSE__")

    purpose_based_model_enabled: bool = Field(
        default=False,
        description="Enable the purpose-based data model (Data Purpose, Data Consumer, Data Producer APIs)",
    )
```

- [ ] **Step 2: Register on FidesplusConfig**

In `src/fidesplus/config/__init__.py`, add:
- Import `PurposeSettings`
- Add `purpose: PurposeSettings = PurposeSettings()` field to `FidesplusConfig`
- Add loading logic in `get_config()` for both try and except branches

- [ ] **Step 3: Create the feature flag dependency**

Add to `src/fidesplus/api/deps.py`:

```python
from fastapi import Depends, HTTPException

def require_purpose_model_enabled(
    config: FidesplusConfig = Depends(get_fidesplus_config),
) -> None:
    """Dependency that returns 404 when purpose-based model is disabled."""
    if not config.purpose.purpose_based_model_enabled:
        raise HTTPException(status_code=404)
```

- [ ] **Step 4: Commit**

```bash
git add src/fidesplus/config/purpose_settings.py src/fidesplus/config/__init__.py src/fidesplus/api/deps.py
git commit -m "feat: add purpose_based_model_enabled feature flag and dependency"
```

---

### Task 10: DataPurposeService

**Files:**
- Create: `src/fidesplus/service/data_purpose/data_purpose_service.py`
- Test: (fidesplus) `tests/ops/service/test_data_purpose_service.py`

- [ ] **Step 1: Write the service test**

```python
# tests/ops/service/test_data_purpose_service.py
import pytest
from sqlalchemy.orm import Session

from fidesplus.service.data_purpose.data_purpose_service import DataPurposeService
from fides.api.models.data_purpose import DataPurpose


@pytest.mark.integration
class TestDataPurposeService:
    def test_create_purpose(self, db: Session):
        service = DataPurposeService(db)
        purpose = service.create(
            fides_key="svc_test_purpose",
            name="Service Test Purpose",
            data_use="marketing.advertising",
        )
        assert purpose.fides_key == "svc_test_purpose"
        assert purpose.data_use == "marketing.advertising"

    def test_create_validates_data_use(self, db: Session):
        service = DataPurposeService(db)
        with pytest.raises(ValueError, match="data_use"):
            service.create(
                fides_key="bad_use",
                name="Bad Use",
                data_use="nonexistent.use.key",
            )

    def test_get_by_fides_key(self, db: Session):
        service = DataPurposeService(db)
        service.create(
            fides_key="get_test",
            name="Get Test",
            data_use="analytics",
        )
        result = service.get_by_fides_key("get_test")
        assert result is not None
        assert result.name == "Get Test"

    def test_get_by_fides_key_not_found(self, db: Session):
        service = DataPurposeService(db)
        result = service.get_by_fides_key("nonexistent")
        assert result is None

    def test_update_purpose(self, db: Session):
        service = DataPurposeService(db)
        service.create(
            fides_key="update_test",
            name="Original Name",
            data_use="analytics",
        )
        updated = service.update("update_test", name="Updated Name")
        assert updated.name == "Updated Name"

    def test_delete_purpose(self, db: Session):
        service = DataPurposeService(db)
        service.create(
            fides_key="delete_test",
            name="Delete Me",
            data_use="analytics",
        )
        service.delete("delete_test")
        assert service.get_by_fides_key("delete_test") is None

    def test_delete_blocked_when_in_use(self, db: Session, system):
        """Deleting a purpose that's linked to a system should fail."""
        service = DataPurposeService(db)
        purpose = service.create(
            fides_key="in_use_purpose",
            name="In Use",
            data_use="analytics",
        )
        # Link purpose to system via SystemPurpose
        from fides.api.models.system_purpose import SystemPurpose
        SystemPurpose.create(
            db=db,
            data={
                "system_id": system.id,
                "data_purpose_id": purpose.id,
            },
        )
        with pytest.raises(Exception):
            service.delete("in_use_purpose")

    def test_force_delete_removes_references(self, db: Session, system):
        service = DataPurposeService(db)
        purpose = service.create(
            fides_key="force_delete_purpose",
            name="Force Delete",
            data_use="analytics",
        )
        from fides.api.models.system_purpose import SystemPurpose
        SystemPurpose.create(
            db=db,
            data={
                "system_id": system.id,
                "data_purpose_id": purpose.id,
            },
        )
        service.delete("force_delete_purpose", force=True)
        assert service.get_by_fides_key("force_delete_purpose") is None

    def test_list_query(self, db: Session):
        service = DataPurposeService(db)
        service.create(fides_key="list_a", name="A", data_use="analytics")
        service.create(fides_key="list_b", name="B", data_use="marketing")
        results = service.list_query().all()
        fides_keys = [r.fides_key for r in results]
        assert "list_a" in fides_keys
        assert "list_b" in fides_keys

    def test_list_query_filter_by_data_use(self, db: Session):
        service = DataPurposeService(db)
        service.create(fides_key="filter_a", name="A", data_use="analytics")
        service.create(fides_key="filter_b", name="B", data_use="marketing")
        results = service.list_query(data_use="analytics").all()
        fides_keys = [r.fides_key for r in results]
        assert "filter_a" in fides_keys
        assert "filter_b" not in fides_keys
```

- [ ] **Step 2: Run test to verify it fails**

Expected: ImportError

- [ ] **Step 3: Write the DataPurposeService**

```python
# src/fidesplus/service/data_purpose/data_purpose_service.py
from typing import List, Optional

from sqlalchemy.orm import Query, Session

from fides.api.models.data_purpose import DataPurpose
from fides.api.models.data_consumer import DataConsumerPurpose
from fides.api.models.system_purpose import SystemPurpose
from fides.api.models.sql_models import DataUse, DataSubject


class DataPurposeService:
    def __init__(self, db: Session):
        self.db = db

    def _validate_data_use(self, data_use: str) -> None:
        exists = self.db.query(DataUse).filter_by(fides_key=data_use).first()
        if not exists:
            raise ValueError(f"Invalid data_use: '{data_use}' not found in taxonomy")

    def _validate_data_subject(self, data_subject: Optional[str]) -> None:
        if data_subject:
            exists = self.db.query(DataSubject).filter_by(fides_key=data_subject).first()
            if not exists:
                raise ValueError(f"Invalid data_subject: '{data_subject}' not found in taxonomy")

    def create(self, *, fides_key: str, name: str, data_use: str, **kwargs) -> DataPurpose:
        self._validate_data_use(data_use)
        self._validate_data_subject(kwargs.get("data_subject"))
        return DataPurpose.create(
            db=self.db,
            data={"fides_key": fides_key, "name": name, "data_use": data_use, **kwargs},
        )

    def get_by_fides_key(self, fides_key: str) -> Optional[DataPurpose]:
        return self.db.query(DataPurpose).filter_by(fides_key=fides_key).first()

    def update(self, fides_key: str, **kwargs) -> DataPurpose:
        purpose = self.get_by_fides_key(fides_key)
        if not purpose:
            raise ValueError(f"DataPurpose '{fides_key}' not found")
        if "data_use" in kwargs and kwargs["data_use"] is not None:
            self._validate_data_use(kwargs["data_use"])
        if "data_subject" in kwargs:
            self._validate_data_subject(kwargs["data_subject"])
        # Filter out None values for partial update
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        return purpose.update(db=self.db, data=update_data)

    def delete(self, fides_key: str, force: bool = False) -> None:
        purpose = self.get_by_fides_key(fides_key)
        if not purpose:
            raise ValueError(f"DataPurpose '{fides_key}' not found")
        if force:
            # Remove all join table references first
            self.db.query(SystemPurpose).filter_by(data_purpose_id=purpose.id).delete()
            self.db.query(DataConsumerPurpose).filter_by(data_purpose_id=purpose.id).delete()
        purpose.delete(self.db)

    def list_query(
        self,
        data_use: Optional[str] = None,
        data_subject: Optional[str] = None,
    ) -> "Query[DataPurpose]":
        """Return a query object for pagination by the route layer."""
        query = self.db.query(DataPurpose)
        if data_use:
            query = query.filter(DataPurpose.data_use == data_use)
        if data_subject:
            query = query.filter(DataPurpose.data_subject == data_subject)
        return query
```

- [ ] **Step 4: Run tests**

Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/fidesplus/service/data_purpose/__init__.py src/fidesplus/service/data_purpose/data_purpose_service.py tests/ops/service/test_data_purpose_service.py
git commit -m "feat: add DataPurposeService with CRUD and validation"
```

---

### Task 11: DataConsumerService (Facade)

**Files:**
- Create: `src/fidesplus/service/data_consumer/data_consumer_service.py`
- Test: (fidesplus) `tests/ops/service/test_data_consumer_service.py`

- [ ] **Step 1: Write the service test**

Key tests to include:
- `test_create_group_consumer` - creates a non-system consumer
- `test_create_system_type_rejected` - returns error for type=system
- `test_get_non_system_consumer` - fetches by ID from data_consumer table
- `test_get_system_consumer` - fetches from ctl_systems with type=system param
- `test_list_unified` - returns both system and non-system consumers
- `test_list_filter_by_type` - filters by type
- `test_assign_purpose_to_system` - writes to system_purpose
- `test_assign_purpose_to_group` - writes to data_consumer_purpose
- `test_remove_purpose_from_system` - deletes from system_purpose
- `test_replace_purposes` - replaces all purposes for a consumer
- `test_system_response_coercion` - tags coalesced to [], type hardcoded to "system"

- [ ] **Step 2: Write the DataConsumerService**

The service should implement:
- `create(data: DataConsumerCreate) -> DataConsumerResponse` - validates type != system, creates in data_consumer table
- `get(id: str, type: Optional[str] = None) -> DataConsumerResponse` - if type=system, query ctl_systems; else query data_consumer
- `list(type: Optional[str], purpose_fides_key: Optional[str], tags: Optional[List[str]]) -> List[DataConsumerResponse]` - query both sources, merge
- `update(id: str, data: DataConsumerUpdate) -> DataConsumerResponse` - non-system only
- `delete(id: str) -> None` - non-system only
- `assign_purposes(id: str, type: Optional[str], purpose_fides_keys: List[str], assigned_by: Optional[str]) -> DataConsumerResponse` - replace semantics
- `add_purpose(id: str, type: Optional[str], purpose_fides_key: str, assigned_by: Optional[str]) -> DataConsumerResponse`
- `remove_purpose(id: str, type: Optional[str], purpose_fides_key: str) -> DataConsumerResponse`
- `_system_to_response(system: System) -> DataConsumerResponse` - facade mapper with coercion:

```python
def _system_to_response(self, system: System) -> DataConsumerResponse:
    """Coerce a System row into the unified DataConsumerResponse schema."""
    purposes = []
    for sp in system.system_purposes:
        purposes.append(DataPurposeResponse.model_validate(sp.data_purpose))

    # Note: data_shared_with_third_parties, third_parties, and shared_categories
    # could be populated from the system's privacy declarations in a future phase.
    # For Phase 1, these are set to None for system-type consumers.
    return DataConsumerResponse(
        id=system.id,
        name=system.name or system.fides_key,
        description=system.description,
        type="system",
        external_id=None,
        purposes=purposes,
        system_fides_key=system.fides_key,
        vendor_id=getattr(system, "vendor_id", None),
        egress=system.egress if isinstance(system.egress, dict) else None,
        ingress=system.ingress if isinstance(system.ingress, dict) else None,
        data_shared_with_third_parties=None,
        third_parties=None,
        shared_categories=None,
        tags=system.tags or [],  # Coalesce None to []
        contact_email=None,
        contact_slack_channel=None,
        contact_details=None,
        created_at=system.created_at,
        updated_at=system.updated_at,
    )
```

- [ ] **Step 3: Run tests**

Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/fidesplus/service/data_consumer/__init__.py src/fidesplus/service/data_consumer/data_consumer_service.py tests/ops/service/test_data_consumer_service.py
git commit -m "feat: add DataConsumerService with facade pattern"
```

---

### Task 12: DataProducerService

**Files:**
- Create: `src/fidesplus/service/data_producer/data_producer_service.py`
- Test: (fidesplus) `tests/ops/service/test_data_producer_service.py`

- [ ] **Step 1: Write the service test**

Key tests:
- `test_create_producer`
- `test_get_producer`
- `test_update_producer`
- `test_delete_producer_nullifies_datasets`
- `test_add_member`
- `test_remove_member`
- `test_replace_members`
- `test_assign_dataset`
- `test_validate_monitor_id`

- [ ] **Step 2: Write the DataProducerService**

The service should implement:
- `create(data: DataProducerCreate) -> DataProducer`
- `get(id: str) -> Optional[DataProducer]`
- `list_query() -> Query[DataProducer]` (returns query for pagination, consistent with DataPurposeService)
- `update(id: str, data: DataProducerUpdate) -> DataProducer`
- `delete(id: str) -> None`
- `set_members(id: str, user_ids: List[str]) -> DataProducer` - replace semantics
- `add_member(id: str, user_id: str) -> DataProducer`
- `remove_member(id: str, user_id: str) -> DataProducer`

- [ ] **Step 3: Run tests**

Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/fidesplus/service/data_producer/__init__.py src/fidesplus/service/data_producer/data_producer_service.py tests/ops/service/test_data_producer_service.py
git commit -m "feat: add DataProducerService with member management"
```

---

## Chunk 3: API Routes (fidesplus)

### Task 13: Register Scopes and URN Paths in Fidesplus

**Files:**
- Modify: `src/fidesplus/api/plus_scope_registry.py`
- Modify: `src/fidesplus/api/urn_registry.py`

- [ ] **Step 1: Define scope constants and register with role mappings**

In `src/fidesplus/api/plus_scope_registry.py`, define the new scope constants (following the existing pattern for fidesplus-only features like `SYSTEM_GROUP`, `DISCOVERY_MONITOR`, etc.):

```python
# Data Purpose scopes
DATA_PURPOSE = "data_purpose"
DATA_PURPOSE_CREATE = f"{DATA_PURPOSE}:{CREATE}"
DATA_PURPOSE_READ = f"{DATA_PURPOSE}:{READ}"
DATA_PURPOSE_UPDATE = f"{DATA_PURPOSE}:{UPDATE}"
DATA_PURPOSE_DELETE = f"{DATA_PURPOSE}:{DELETE}"

# Data Consumer scopes
DATA_CONSUMER = "data_consumer"
DATA_CONSUMER_CREATE = f"{DATA_CONSUMER}:{CREATE}"
DATA_CONSUMER_READ = f"{DATA_CONSUMER}:{READ}"
DATA_CONSUMER_UPDATE = f"{DATA_CONSUMER}:{UPDATE}"
DATA_CONSUMER_DELETE = f"{DATA_CONSUMER}:{DELETE}"

# Data Producer scopes
DATA_PRODUCER = "data_producer"
DATA_PRODUCER_CREATE = f"{DATA_PRODUCER}:{CREATE}"
DATA_PRODUCER_READ = f"{DATA_PRODUCER}:{READ}"
DATA_PRODUCER_UPDATE = f"{DATA_PRODUCER}:{UPDATE}"
DATA_PRODUCER_DELETE = f"{DATA_PRODUCER}:{DELETE}"
```

Add to `UPDATED_SCOPE_DOCS`:
```python
DATA_PURPOSE_CREATE: "Create data purposes",
DATA_PURPOSE_READ: "Read data purposes",
DATA_PURPOSE_UPDATE: "Update data purposes",
DATA_PURPOSE_DELETE: "Delete data purposes",
DATA_CONSUMER_CREATE: "Create data consumers",
DATA_CONSUMER_READ: "Read data consumers",
DATA_CONSUMER_UPDATE: "Update data consumers",
DATA_CONSUMER_DELETE: "Delete data consumers",
DATA_PRODUCER_CREATE: "Create data producers",
DATA_PRODUCER_READ: "Read data producers",
DATA_PRODUCER_UPDATE: "Update data producers",
DATA_PRODUCER_DELETE: "Delete data producers",
```

Add all 12 scopes to `PLUS_OWNER_SCOPES`. Add the READ scopes to `PLUS_VIEWER_SCOPES`. Add CREATE/READ/UPDATE to `PLUS_CONTRIBUTOR_SCOPES`. Follow the existing pattern in the file for how scopes are grouped by role.

- [ ] **Step 2: Add URN registry entries**

In `src/fidesplus/api/urn_registry.py`, add URL path constants:

```python
DATA_PURPOSE = "/data-purpose"
DATA_PURPOSE_DETAIL = "/data-purpose/{fides_key}"
DATA_CONSUMER = "/data-consumer"
DATA_CONSUMER_DETAIL = "/data-consumer/{id}"
DATA_CONSUMER_PURPOSE = "/data-consumer/{id}/purpose"
DATA_CONSUMER_PURPOSE_DETAIL = "/data-consumer/{id}/purpose/{fides_key}"
DATA_PRODUCER = "/data-producer"
DATA_PRODUCER_DETAIL = "/data-producer/{id}"
DATA_PRODUCER_MEMBER = "/data-producer/{id}/member"
DATA_PRODUCER_MEMBER_DETAIL = "/data-producer/{id}/member/{user_id}"
```

- [ ] **Step 3: Commit**

```bash
git add src/fidesplus/api/plus_scope_registry.py src/fidesplus/api/urn_registry.py
git commit -m "feat: register purpose-based data model scopes and URN paths in fidesplus"
```

---

### Task 14: DataPurpose Routes

**Files:**
- Create: `src/fidesplus/api/routes/data_purpose.py`
- Test: (fidesplus) `tests/ops/api/test_data_purpose_api.py`

- [ ] **Step 1: Write the API test**

Key tests:
- `test_create_purpose` - POST /data-purpose, 201
- `test_create_purpose_invalid_data_use` - POST, 422
- `test_get_purpose` - GET /data-purpose/{fides_key}, 200
- `test_get_purpose_not_found` - GET, 404
- `test_list_purposes` - GET /data-purpose, 200
- `test_list_filter_by_data_use` - GET /data-purpose?data_use=analytics, 200
- `test_update_purpose` - PUT /data-purpose/{fides_key}, 200
- `test_delete_purpose` - DELETE /data-purpose/{fides_key}, 204
- `test_delete_purpose_in_use` - DELETE, 409
- `test_delete_purpose_force` - DELETE ?force=true, 204
- `test_unauthorized` - all endpoints without auth, 401
- `test_feature_flag_off` - endpoints return 404 when disabled

- [ ] **Step 2: Write the routes**

**Important patterns:** Use `fides.api.util.api_router.APIRouter` (not plain `fastapi.APIRouter`). Use `Optional[str]` (not `str | None`). Add `require_purpose_model_enabled` as a router-level dependency so all routes return 404 when the feature flag is off. Use `fastapi_pagination.ext.sqlalchemy.paginate()` for pagination.

```python
# src/fidesplus/api/routes/data_purpose.py
from typing import Optional

from fastapi import Depends, HTTPException, Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from fides.api.deps import get_db
from fides.api.schemas.data_purpose import DataPurposeCreate, DataPurposeResponse, DataPurposeUpdate
from fides.api.util.api_router import APIRouter
from fidesplus.api.plus_scope_registry import DATA_PURPOSE_CREATE, DATA_PURPOSE_DELETE, DATA_PURPOSE_READ, DATA_PURPOSE_UPDATE
from fidesplus.api.deps import require_purpose_model_enabled
from fidesplus.api.plus_scope_registry import verify_oauth_client_plus
from fidesplus.service.data_purpose.data_purpose_service import DataPurposeService

router = APIRouter(
    prefix="/data-purpose",
    tags=["Data Purpose"],
    dependencies=[Depends(require_purpose_model_enabled)],
)


@router.post(
    "",
    response_model=DataPurposeResponse,
    status_code=HTTP_201_CREATED,
    dependencies=[Security(verify_oauth_client_plus, scopes=[DATA_PURPOSE_CREATE])],
)
def create_data_purpose(
    data: DataPurposeCreate,
    db: Session = Depends(get_db),
) -> DataPurposeResponse:
    service = DataPurposeService(db)
    return service.create(**data.model_dump())


@router.get(
    "",
    response_model=Page[DataPurposeResponse],
    dependencies=[Security(verify_oauth_client_plus, scopes=[DATA_PURPOSE_READ])],
)
def list_data_purposes(
    data_use: Optional[str] = Query(None),
    data_subject: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    params: Params = Depends(),
) -> Page[DataPurposeResponse]:
    service = DataPurposeService(db)
    query = service.list_query(data_use=data_use, data_subject=data_subject)
    return paginate(query, params)


@router.get(
    "/{fides_key}",
    response_model=DataPurposeResponse,
    dependencies=[Security(verify_oauth_client_plus, scopes=[DATA_PURPOSE_READ])],
)
def get_data_purpose(
    fides_key: str,
    db: Session = Depends(get_db),
) -> DataPurposeResponse:
    service = DataPurposeService(db)
    purpose = service.get_by_fides_key(fides_key)
    if not purpose:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    return purpose


@router.put(
    "/{fides_key}",
    response_model=DataPurposeResponse,
    dependencies=[Security(verify_oauth_client_plus, scopes=[DATA_PURPOSE_UPDATE])],
)
def update_data_purpose(
    fides_key: str,
    data: DataPurposeUpdate,
    db: Session = Depends(get_db),
) -> DataPurposeResponse:
    service = DataPurposeService(db)
    return service.update(fides_key, **data.model_dump(exclude_unset=True))


@router.delete(
    "/{fides_key}",
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Security(verify_oauth_client_plus, scopes=[DATA_PURPOSE_DELETE])],
)
def delete_data_purpose(
    fides_key: str,
    force: bool = Query(False),
    db: Session = Depends(get_db),
) -> None:
    service = DataPurposeService(db)
    service.delete(fides_key, force=force)
```

- [ ] **Step 3: Mount the router**

In `src/fidesplus/main.py:prepare_plus_app()`, add to the `plus_router` registrations (routes will be under `/api/v1/plus/`):

```python
from fidesplus.api.routes.data_purpose import router as data_purpose_router
plus_router.include_router(data_purpose_router)
```

- [ ] **Step 4: Run API tests**

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/fidesplus/api/routes/data_purpose.py tests/ops/api/test_data_purpose_api.py
git commit -m "feat: add DataPurpose CRUD API routes"
```

---

### Task 15: DataConsumer Routes

**Files:**
- Create: `src/fidesplus/api/routes/data_consumer.py`
- Test: (fidesplus) `tests/ops/api/test_data_consumer_api.py`

- [ ] **Step 1: Write the API test**

Key tests:
- `test_create_group_consumer` - POST /data-consumer with type=group, 201
- `test_create_system_type_rejected` - POST with type=system, 400
- `test_get_non_system_consumer` - GET /data-consumer/{id}, 200
- `test_get_system_consumer` - GET /data-consumer/{id}?type=system, 200
- `test_get_without_type_param_not_found_for_system` - GET /data-consumer/{system_id} (no type param), 404
- `test_list_consumers_unified` - GET /data-consumer, returns both types
- `test_list_filter_by_type` - GET /data-consumer?type=group
- `test_update_non_system` - PUT /data-consumer/{id}, 200
- `test_update_system_type_rejected` - PUT with system id + ?type=system, 400
- `test_delete_non_system` - DELETE /data-consumer/{id}, 204
- `test_assign_purposes_to_system` - PUT /data-consumer/{id}/purpose?type=system, 200
- `test_assign_purposes_to_group` - PUT /data-consumer/{id}/purpose, 200
- `test_add_single_purpose` - POST /data-consumer/{id}/purpose/{fides_key}, 200
- `test_remove_purpose` - DELETE /data-consumer/{id}/purpose/{fides_key}, 204

- [ ] **Step 2: Write the routes**

**Important patterns:** Use `fides.api.util.api_router.APIRouter` (not plain `fastapi.APIRouter`). Use `Optional[str]` (not `str | None`). Add `require_purpose_model_enabled` as a router-level dependency. Use `fastapi_pagination.ext.sqlalchemy.paginate()` for the list endpoint. The `?type=system` query param controls routing to the facade.

```python
# src/fidesplus/api/routes/data_consumer.py
from typing import Optional

from fastapi import Depends, HTTPException, Query, Security
from fastapi_pagination import Page, Params
from sqlalchemy.orm import Session
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.deps import get_db
from fides.api.schemas.data_consumer import (
    DataConsumerCreate,
    DataConsumerPurposeAssignment,
    DataConsumerResponse,
    DataConsumerUpdate,
)
from fides.api.util.api_router import APIRouter
from fidesplus.api.plus_scope_registry import (
    DATA_CONSUMER_CREATE,
    DATA_CONSUMER_DELETE,
    DATA_CONSUMER_READ,
    DATA_CONSUMER_UPDATE,
)
from fidesplus.api.deps import require_purpose_model_enabled
from fidesplus.api.plus_scope_registry import verify_oauth_client_plus
from fidesplus.service.data_consumer.data_consumer_service import DataConsumerService

router = APIRouter(
    prefix="/data-consumer",
    tags=["Data Consumer"],
    dependencies=[Depends(require_purpose_model_enabled)],
)
```

Implement all CRUD routes + purpose assignment sub-routes (`PUT /{id}/purpose`, `POST /{id}/purpose/{fides_key}`, `DELETE /{id}/purpose/{fides_key}`). System-type consumers are read-only (no create/update/delete); the `?type=system` query param triggers the facade path.

**Important:** Purpose assignment endpoints for system-type consumers (`?type=system`) must additionally verify the `system:update` scope (`SYSTEM_UPDATE` from `fides.common.scope_registry`). Add a runtime scope check in the route handler:

```python
from fides.common.scope_registry import SYSTEM_UPDATE

# In purpose assignment handlers, when type == "system":
if consumer_type == "system":
    # verify_oauth_client_plus already ran via Security dependency;
    # additionally check SYSTEM_UPDATE scope
    verify_oauth_client_plus(security_scopes=SecurityScopes(scopes=[SYSTEM_UPDATE]), authorization=authorization)
```

- [ ] **Step 3: Mount the router**

In the fidesplus router registration file, add:
```python
from fidesplus.api.routes.data_consumer import router as data_consumer_router
plus_router.include_router(data_consumer_router)
```

- [ ] **Step 4: Run API tests**

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/fidesplus/api/routes/data_consumer.py tests/ops/api/test_data_consumer_api.py
git commit -m "feat: add DataConsumer CRUD and purpose assignment API routes"
```

---

### Task 16: DataProducer Routes

**Files:**
- Create: `src/fidesplus/api/routes/data_producer.py`
- Test: (fidesplus) `tests/ops/api/test_data_producer_api.py`

- [ ] **Step 1: Write the API test**

Key tests:
- `test_create_producer` - POST /data-producer, 201
- `test_get_producer` - GET /data-producer/{id}, 200
- `test_list_producers` - GET /data-producer, 200
- `test_update_producer` - PUT /data-producer/{id}, 200
- `test_delete_producer` - DELETE /data-producer/{id}, 204
- `test_set_members` - PUT /data-producer/{id}/member, 200
- `test_add_member` - POST /data-producer/{id}/member/{user_id}, 200
- `test_remove_member` - DELETE /data-producer/{id}/member/{user_id}, 204

- [ ] **Step 2: Write the routes**

**Important patterns:** Use `fides.api.util.api_router.APIRouter` (not plain `fastapi.APIRouter`). Use `Optional[str]` (not `str | None`). Add `require_purpose_model_enabled` as a router-level dependency. Use `fastapi_pagination.ext.sqlalchemy.paginate()` for the list endpoint.

```python
# src/fidesplus/api/routes/data_producer.py
from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from sqlalchemy.orm import Session
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from fides.api.deps import get_db
from fides.api.schemas.data_producer import (
    DataProducerCreate,
    DataProducerMemberAssignment,
    DataProducerResponse,
    DataProducerUpdate,
)
from fides.api.util.api_router import APIRouter
from fidesplus.api.plus_scope_registry import (
    DATA_PRODUCER_CREATE,
    DATA_PRODUCER_DELETE,
    DATA_PRODUCER_READ,
    DATA_PRODUCER_UPDATE,
)
from fidesplus.api.deps import require_purpose_model_enabled
from fidesplus.api.plus_scope_registry import verify_oauth_client_plus
from fidesplus.service.data_producer.data_producer_service import DataProducerService

router = APIRouter(
    prefix="/data-producer",
    tags=["Data Producer"],
    dependencies=[Depends(require_purpose_model_enabled)],
)
```

Implement CRUD routes + member management sub-routes (`PUT /{id}/member`, `POST /{id}/member/{user_id}`, `DELETE /{id}/member/{user_id}`).

- [ ] **Step 3: Mount the router**

In the fidesplus router registration file, add:
```python
from fidesplus.api.routes.data_producer import router as data_producer_router
plus_router.include_router(data_producer_router)
```

- [ ] **Step 4: Run API tests**

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/fidesplus/api/routes/data_producer.py tests/ops/api/test_data_producer_api.py
git commit -m "feat: add DataProducer CRUD and member management API routes"
```

---

## Chunk 4: Dataset Integration and Final Verification

### Task 17: Dataset Purpose Validation in Write Path

**Files:**
- Modify: existing dataset service/endpoint in fidesplus (find the dataset write handler)
- Test: extend existing dataset API tests

- [ ] **Step 1: Find the dataset write handler**

Locate where dataset create/update is handled in fidesplus. The handler needs to be extended to:
1. Validate `data_purposes` fides_key strings at dataset level against `data_purpose` table
2. Validate `data_purposes` strings within collection/field/sub-field JSON
3. Validate `data_producer_id` references a valid `DataProducer`
4. Pass through when feature flag is off (ignore new fields)

- [ ] **Step 2: Write the validation test**

Key tests:
- `test_create_dataset_with_valid_purposes` - purposes validated, stored
- `test_create_dataset_with_invalid_purpose` - 422 for nonexistent fides_key
- `test_create_dataset_with_collection_purposes` - collection-level purposes in JSON
- `test_create_dataset_with_field_purposes` - field-level purposes in JSON
- `test_create_dataset_with_producer` - valid data_producer_id
- `test_create_dataset_with_invalid_producer` - 422 for nonexistent producer
- `test_existing_dataset_payloads_unaffected` - backward compatibility
- `test_feature_flag_off_ignores_purposes` - new fields stripped when disabled

- [ ] **Step 3: Implement the validation**

Add purpose validation to the dataset write path. Extract a helper that recursively validates `data_purposes` arrays at all levels of the collections JSON.

```python
def validate_dataset_purposes(db: Session, dataset_data: dict) -> None:
    """Validate all data_purposes references in a dataset payload."""
    all_purpose_keys = set()

    # Dataset-level purposes
    if dataset_data.get("data_purposes"):
        all_purpose_keys.update(dataset_data["data_purposes"])

    # Collection/field/sub-field purposes (recursive)
    def collect_purposes(obj):
        if isinstance(obj, dict):
            if obj.get("data_purposes"):
                all_purpose_keys.update(obj["data_purposes"])
            for value in obj.values():
                collect_purposes(value)
        elif isinstance(obj, list):
            for item in obj:
                collect_purposes(item)

    collect_purposes(dataset_data.get("collections", []))

    # Validate all collected keys exist
    if all_purpose_keys:
        existing = {
            p.fides_key
            for p in db.query(DataPurpose.fides_key)
            .filter(DataPurpose.fides_key.in_(all_purpose_keys))
            .all()
        }
        missing = all_purpose_keys - existing
        if missing:
            raise ValueError(f"Invalid data_purposes references: {missing}")
```

- [ ] **Step 4: Run tests**

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
# Add the specific files modified for dataset purpose validation
git add src/fidesplus/service/dataset/ tests/ops/api/test_dataset_purpose_validation.py
git commit -m "feat: add dataset purpose validation in write path"
```

---

### Task 18: End-to-End Verification

- [ ] **Step 1: Run the full model test suite**

```bash
nox -s "pytest(ops-unit)" -- tests/ops/models/test_data_purpose.py tests/ops/models/test_data_consumer.py tests/ops/models/test_system_purpose.py tests/ops/models/test_data_producer.py tests/ops/models/test_dataset_purposes.py -v
```

Expected: All model tests PASS

- [ ] **Step 2: Run static checks**

```bash
nox -s static_checks
```

Expected: ruff format, ruff lint, mypy all pass

- [ ] **Step 3: Run the full fidesplus service + API test suite**

Run all new service and API tests together.

Expected: All tests PASS

- [ ] **Step 4: Check migrations**

```bash
nox -s check_migrations
```

Expected: No missing migrations

- [ ] **Step 5: Run existing test suites to check backward compatibility**

```bash
nox -s "pytest(ops-unit)" -- tests/ops/models/ -v --timeout=300
nox -s "pytest(ctl-unit)" -- tests/ctl/ -v --timeout=300
```

Expected: No regressions in existing tests

- [ ] **Step 6: Final commit (if any fixups needed)**

```bash
git commit -m "fix: address any issues found during e2e verification"
```

---

## Summary

| Chunk | Tasks | What it delivers |
|-------|-------|-----------------|
| **1: Models & Migration** | Tasks 1-8 | All SQLAlchemy models, Alembic migration, Pydantic schemas, permission scopes |
| **2: Services** | Tasks 9-12 | Feature flag, DataPurposeService, DataConsumerService (facade), DataProducerService |
| **3: API Routes** | Tasks 13-16 | All REST endpoints mounted and tested |
| **4: Integration** | Tasks 17-18 | Dataset purpose validation, end-to-end verification, backward compat confirmation |
