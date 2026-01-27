import pytest

from fides.api.schemas.saas.shared_schemas import PollingStatusResult

@pytest.mark.async_dsr
class TestPollingStatusResult:
    """
    Base tests for PollingStatusResult model
    To be expanded if there are additional logics for the PollingStatusResult model
    """

    def test_init_default(self):
        status_result = PollingStatusResult(is_complete=True)
        assert status_result.skip_result_request == False
        pass

    def test_init_skip_result(self):
        status_result = PollingStatusResult(is_complete=True, skip_result_request=True)
        assert status_result.skip_result_request == True
        pass

    def test_dict_output(self):
        status_result = PollingStatusResult(is_complete=True, skip_result_request=True)
        assert status_result.dict() == {
            "is_complete": True,
            "skip_result_request": True,
        }
        pass
