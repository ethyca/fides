from fides.api.graph.config import ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS
from fides.api.models.privacy_request import ExecutionLogStatus
from fides.api.schemas.policy import ActionType


class TestRequestTask:
    def test_basic_attributes(self, db, request_task, privacy_request):
        assert privacy_request.access_tasks.count() == 3
        assert request_task.privacy_request_id == privacy_request.id
        assert request_task.privacy_request == privacy_request
        assert request_task.action_type == ActionType.access

        assert (
            privacy_request.get_existing_request_task(
                db, ActionType.access, request_task.request_task_address
            )
            == request_task
        )
        assert (
            privacy_request.get_tasks_by_action(ActionType.access).all()
            == privacy_request.access_tasks.all()
        )
        assert privacy_request.get_tasks_by_action(ActionType.erasure).all() == []
        assert privacy_request.get_tasks_by_action(ActionType.consent).all() == []

    def test_get_pending_downstream_tasks(self, db, request_task):
        root_task = request_task.get_tasks_with_same_action_type(
            db, ROOT_COLLECTION_ADDRESS.value
        ).first()
        terminator_task = request_task.get_tasks_with_same_action_type(
            db, TERMINATOR_ADDRESS.value
        ).first()

        assert root_task.get_pending_downstream_tasks(db).all() == [request_task]
        assert request_task.get_pending_downstream_tasks(db).all() == [terminator_task]
        assert terminator_task.get_pending_downstream_tasks(db).all() == []

    def test_upstream_tasks_complete(self, db, request_task):
        # The Request Task only has the Root Task upstream, which is complete
        assert request_task.upstream_tasks == [ROOT_COLLECTION_ADDRESS.value]
        assert request_task.upstream_tasks_complete(db)

        # The root Task has nothing upstream
        root_task = request_task.get_tasks_with_same_action_type(
            db, ROOT_COLLECTION_ADDRESS.value
        ).first()
        assert root_task.status == ExecutionLogStatus.complete
        assert root_task.is_root_task
        assert root_task.upstream_tasks_complete(db)

        # The Terminator task has the request task upstream which is pending
        terminator_task = request_task.get_tasks_with_same_action_type(
            db, TERMINATOR_ADDRESS.value
        ).first()
        assert terminator_task.is_terminator_task
        assert terminator_task.upstream_tasks == [request_task.collection_address]
        assert request_task.status == ExecutionLogStatus.pending
        assert not terminator_task.upstream_tasks_complete(db)

        # Set the request task to be skipped
        request_task.update_status(db, ExecutionLogStatus.skipped)
        # Skipped is considered to be a completed state
        assert terminator_task.upstream_tasks_complete(db)

    def test_update_status(self, db, request_task):
        assert request_task.status == ExecutionLogStatus.pending
        request_task.update_status(db, ExecutionLogStatus.complete)

        assert request_task.status == ExecutionLogStatus.complete
