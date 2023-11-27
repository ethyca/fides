from fides.api.models.system_compass_sync import SystemCompassSync


class TestSystemGVLSync:
    def test_system_compass_sync(self, db, system):
        start_sync = SystemCompassSync.start_system_sync(db)
        assert start_sync.id
        assert start_sync.created_at
        assert start_sync.updated_at
        assert start_sync.sync_started_at
        assert not start_sync.sync_completed_at
        assert not start_sync.updated_systems

        start_sync.finish_system_sync(db, updated_systems=[system.id])

        db.refresh(start_sync)

        assert start_sync.sync_completed_at
        assert start_sync.sync_completed_at > start_sync.sync_started_at
        assert start_sync.updated_systems == [system.id]
