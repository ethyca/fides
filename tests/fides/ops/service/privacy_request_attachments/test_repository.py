"""Tests for AttachmentUserProvidedRepository."""

from datetime import datetime, timedelta, timezone

import pytest

from fides.api.models.attachment import (
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    InvalidAttachmentStateError,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_repository import (
    AttachmentUserProvidedRepository,
)

UPLOADED = AttachmentUserProvidedStatus.uploaded
PROMOTED = AttachmentUserProvidedStatus.promoted
DELETED = AttachmentUserProvidedStatus.deleted


@pytest.fixture
def repo() -> AttachmentUserProvidedRepository:
    return AttachmentUserProvidedRepository()


@pytest.fixture
def insert_row(db, storage_config_default):
    """Insert rows; auto-clean on teardown. ``.track(id)`` registers a row
    inserted via the repository for the same teardown sweep."""
    created: list[str] = []

    def _factory(
        *,
        object_key: str = "privacy_request_attachments/file.pdf",
        status: AttachmentUserProvidedStatus = UPLOADED,
        created_at: datetime | None = None,
    ) -> AttachmentUserProvided:
        row = AttachmentUserProvided(
            object_key=object_key,
            status=status,
            storage_key=storage_config_default.key,
            field_name="passport",
            property_id="prop_xyz",
            policy_key="default_access_policy",
        )
        if created_at is not None:
            row.created_at = created_at
        db.add(row)
        db.flush()
        db.refresh(row)
        created.append(row.id)
        return row

    _factory.track = created.append  # type: ignore[attr-defined]
    yield _factory
    if created:
        db.query(AttachmentUserProvided).filter(
            AttachmentUserProvided.id.in_(created)
        ).delete(synchronize_session=False)
        db.commit()


@pytest.fixture
def uploaded_row(insert_row) -> AttachmentUserProvided:
    return insert_row()


def test_create_uploaded_persists_row(repo, db, storage_config_default, insert_row):
    record = repo.create_uploaded(
        object_key="privacy_request_attachments/flush.pdf",
        storage_key=storage_config_default.key,
        field_name="passport",
        property_id="prop_xyz",
        policy_key="default_access_policy",
        session=db,
    )
    insert_row.track(record.id)
    assert record.id and record.status == UPLOADED
    assert record.object_key == "privacy_request_attachments/flush.pdf"
    assert record.created_at is not None
    assert (record.field_name, record.property_id, record.policy_key) == (
        "passport",
        "prop_xyz",
        "default_access_policy",
    )


def test_lock_by_ids_keys_dict_and_returns_any_state(repo, db, insert_row):
    a = insert_row(object_key="prefix/a.pdf")
    b = insert_row(object_key="prefix/b.pdf", status=PROMOTED)
    locked = repo.lock_by_ids([a.id, b.id, "att_missing"], session=db)
    assert set(locked.keys()) == {a.id, b.id}
    assert locked[a.id].status == UPLOADED
    assert locked[b.id].status == PROMOTED


def test_lock_by_ids_empty_list_short_circuits(repo, db):
    assert repo.lock_by_ids([], session=db) == {}


def test_assert_all_uploaded_passes(repo, uploaded_row):
    repo.assert_all_uploaded([uploaded_row])


def test_assert_all_uploaded_raises_on_non_uploaded(repo, insert_row):
    with pytest.raises(InvalidAttachmentStateError):
        repo.assert_all_uploaded([insert_row(status=PROMOTED)])


class TestMarkPromoted:
    @pytest.mark.parametrize(
        "explicit_ts",
        [None, datetime(2026, 1, 1, tzinfo=timezone.utc)],
    )
    def test_flips_status_and_sets_promoted_at(
        self, repo, db, uploaded_row, explicit_ts
    ):
        repo.mark_promoted(uploaded_row, promoted_at=explicit_ts)
        db.flush()
        db.refresh(uploaded_row)
        assert uploaded_row.status == PROMOTED
        if explicit_ts is None:
            assert uploaded_row.promoted_at is not None
        else:
            assert uploaded_row.promoted_at == explicit_ts

    @pytest.mark.parametrize("prior_status", [PROMOTED, DELETED])
    def test_raises_on_non_uploaded(self, repo, db, insert_row, prior_status):
        row = insert_row(status=prior_status)
        with pytest.raises(InvalidAttachmentStateError):
            repo.mark_promoted(row)
        db.refresh(row)
        assert row.status == prior_status


def test_mark_deleted_in_session_only(repo, db, uploaded_row):
    repo.mark_deleted(uploaded_row)
    assert uploaded_row.status == DELETED
    db.flush()
    db.refresh(uploaded_row)
    assert uploaded_row.status == DELETED


def test_list_uploaded_older_than(repo, db, insert_row):
    old = datetime(2020, 1, 1, tzinfo=timezone.utc)
    cutoff = datetime(2021, 1, 1, tzinfo=timezone.utc)
    future = datetime.now(timezone.utc) + timedelta(days=1)
    old_uploaded = insert_row(object_key="prefix/old_uploaded.pdf", created_at=old)
    new_uploaded = insert_row(object_key="prefix/new_uploaded.pdf", created_at=future)
    old_promoted = insert_row(
        object_key="prefix/old_promoted.pdf", status=PROMOTED, created_at=old
    )
    boundary = insert_row(object_key="prefix/boundary.pdf", created_at=cutoff)
    ret_ids = {r.id for r in repo.list_uploaded_older_than(cutoff, session=db)}
    assert old_uploaded.id in ret_ids
    assert new_uploaded.id not in ret_ids  # too new
    assert old_promoted.id not in ret_ids  # not uploaded
    assert boundary.id not in ret_ids  # cutoff is exclusive


def test_list_uploaded_older_than_caps_and_orders_oldest_first(repo, db, insert_row):
    cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)
    oldest = insert_row(
        object_key="prefix/oldest.pdf",
        created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    middle = insert_row(
        object_key="prefix/middle.pdf",
        created_at=datetime(2021, 1, 1, tzinfo=timezone.utc),
    )
    newest = insert_row(
        object_key="prefix/newest.pdf",
        created_at=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    capped = repo.list_uploaded_older_than(cutoff, limit=2, session=db)
    assert [r.id for r in capped] == [oldest.id, middle.id]
    assert newest.id not in {r.id for r in capped}
