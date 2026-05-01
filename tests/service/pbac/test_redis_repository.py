"""Unit tests for the RedisRepository base class."""

import json
from dataclasses import dataclass
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi_pagination import Params

from fides.service.pbac.redis_repository import RedisRepository

TTL = 604800  # 7 days


@dataclass
class SampleEntity:
    id: str
    name: str
    category: str
    created_at: datetime


class SampleRepository(RedisRepository[SampleEntity]):
    PREFIX = "sample"

    def _serialize(self, entity: SampleEntity) -> str:
        return json.dumps(
            {
                "id": entity.id,
                "name": entity.name,
                "category": entity.category,
                "created_at": entity.created_at.isoformat(),
            }
        )

    def _deserialize(self, data: str) -> SampleEntity:
        d = json.loads(data)
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        return SampleEntity(**d)

    def _get_pk(self, entity: SampleEntity) -> str:
        return entity.id

    def _get_index_entries(self, entity: SampleEntity) -> list[tuple[str, str]]:
        return [("category", entity.category)]


@pytest.fixture()
def mock_cache():
    cache = MagicMock()
    cache.pipeline.return_value = MagicMock()
    cache.pipeline.return_value.execute.return_value = None
    return cache


@pytest.fixture()
def repo(mock_cache):
    return SampleRepository(mock_cache, ttl_seconds=TTL)


@pytest.fixture()
def sample_entity():
    return SampleEntity(
        id="abc123",
        name="Test Entity",
        category="widgets",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


class TestSaveTTL:
    """Verify that save() applies TTL to all Redis keys."""

    def test_entity_key_has_ttl(self, repo, mock_cache, sample_entity):
        mock_cache.get.return_value = None
        repo.save(sample_entity)

        pipe = mock_cache.pipeline.return_value
        pipe.set.assert_called_once_with(
            "sample:abc123", repo._serialize(sample_entity), ex=TTL
        )

    def test_all_key_has_ttl(self, repo, mock_cache, sample_entity):
        mock_cache.get.return_value = None
        repo.save(sample_entity)

        pipe = mock_cache.pipeline.return_value
        pipe.sadd.assert_any_call("sample:_all", "abc123")
        pipe.expire.assert_any_call("sample:_all", TTL)

    def test_index_keys_have_ttl(self, repo, mock_cache, sample_entity):
        mock_cache.get.return_value = None
        repo.save(sample_entity)

        pipe = mock_cache.pipeline.return_value
        pipe.sadd.assert_any_call("sample:idx:category:widgets", "abc123")
        pipe.expire.assert_any_call("sample:idx:category:widgets", TTL)

    def test_pipeline_is_executed(self, repo, mock_cache, sample_entity):
        mock_cache.get.return_value = None
        repo.save(sample_entity)

        pipe = mock_cache.pipeline.return_value
        pipe.execute.assert_called_once()

    def test_update_cleans_stale_indexes_with_ttl(self, repo, mock_cache, sample_entity):
        old_entity = SampleEntity(
            id="abc123",
            name="Old",
            category="old_category",
            created_at=datetime(2024, 1, 1),
        )
        mock_cache.get.return_value = repo._serialize(old_entity)
        repo.save(sample_entity)

        pipe = mock_cache.pipeline.return_value
        # Old index entry removed
        pipe.srem.assert_any_call("sample:idx:category:old_category", "abc123")
        # New entity key still gets TTL
        pipe.set.assert_called_once_with(
            "sample:abc123", repo._serialize(sample_entity), ex=TTL
        )

    @patch("fides.service.pbac.redis_repository.CONFIG")
    def test_defaults_to_config_ttl(self, mock_config, mock_cache):
        mock_config.redis.default_ttl_seconds = 86400
        repo = SampleRepository(mock_cache)
        assert repo._ttl_seconds == 86400


class TestDelete:
    def test_delete_existing(self, repo, mock_cache, sample_entity):
        mock_cache.get.return_value = repo._serialize(sample_entity)
        result = repo.delete("abc123")

        assert result is True
        pipe = mock_cache.pipeline.return_value
        pipe.delete.assert_called_once_with("sample:abc123")
        pipe.srem.assert_any_call("sample:_all", "abc123")
        pipe.srem.assert_any_call("sample:idx:category:widgets", "abc123")
        pipe.execute.assert_called()

    def test_delete_missing(self, repo, mock_cache):
        mock_cache.get.return_value = None
        result = repo.delete("nonexistent")
        assert result is False


