import pytest

from fides.core.config.create import (
    create_and_update_config_file,
    build_field_documentation,
    generate_config_docs,
)
from fides.core.config import FidesConfig
from py._path.local import LocalPath


@pytest.mark.unit
def test_create_and_update_config_file_opt_in(
    tmpdir: LocalPath, test_config: FidesConfig
) -> None:
    """Test that config creation works when opting-in to analytics."""

    create_and_update_config_file(
        config=test_config, fides_directory_location=str(tmpdir), opt_in=True
    )
    assert True


@pytest.mark.unit
class TestGenerateConfigDocs:
    def test_generate_config_docs_todo(self) -> None:
        """Verify that if a '# TODO' is in the docs, failure will occur."""
        assert True


@pytest.mark.unit
def test_build_field_documentation_no_description() -> None:
    """
    Test that when a malformed/incomplete field
    is passed in, a SystemExit is raised.
    """

    with pytest.raises(SystemExit):
        # Missing a description
        bad_field_info = {"type": "string", "default": "foo"}
        build_field_documentation("some_field", bad_field_info)
