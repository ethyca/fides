import os
from dataclasses import dataclass
from typing import Optional

from nox import Session

from constants_nox import (
    EXEC_UV,
    LOGIN,
    START_APP,
)

TOTAL_SPLITS = os.environ.get("TOTAL_SPLITS")
SPLIT_GROUP = os.environ.get("SPLIT_GROUP")


@dataclass
class CoverageConfig:
    report_format: str = "xml"
    cov_name: str = "fides"
    branch_coverage: bool = True
    skip_on_fail: bool = True

    def __str__(self):
        return " ".join(self.args)

    @property
    def args(self) -> list[str]:
        return [
            f"--cov={self.cov_name}",
            f"--cov-report={self.report_format}",
            "--cov-branch" if self.branch_coverage else "",
            "--no-cov-on-fail" if self.skip_on_fail else "",
        ]


@dataclass
class XdistConfig:
    parallel_runners: str = "auto"

    def __str__(self):
        return " ".join(self.args)

    @property
    def args(self) -> list[str]:
        return ["-n", self.parallel_runners]


@dataclass
class ReportConfig:
    report_file: str = "test_report.xml"
    report_format: str = "xml"

    def __str__(self):
        return " ".join(self.args)

    @property
    def args(self) -> list[str]:
        if self.report_format == "xml":
            return [
                "--junitxml",
                self.report_file,
            ]

        return []


@dataclass
class PytestConfig:
    xdist_config: Optional[XdistConfig] = None
    coverage_config: Optional[CoverageConfig] = None
    report_config: Optional[ReportConfig] = None
    suppress_stdout: bool = True
    suppress_warnings: bool = True

    @property
    def args(self) -> list[str]:
        return [
            *self.xdist_config.args,
            *self.coverage_config.args,
            *self.report_config.args,
            "-x",
            "-s" if self.suppress_stdout else "",
            "-W ignore" if self.suppress_warnings else "",
        ]


def _split_args() -> tuple:
    """Return pytest-split CLI args if TOTAL_SPLITS and SPLIT_GROUP are set."""
    if TOTAL_SPLITS and SPLIT_GROUP:
        return (
            "--splits",
            TOTAL_SPLITS,
            "--group",
            SPLIT_GROUP,
            "--splitting-algorithm=least_duration",
        )
    return ()


def _run_pytest(
    session: Session,
    pytest_config: PytestConfig,
    test_dir: str,
    extra_args: tuple = (),
) -> None:
    """Run pytest inside the Docker container."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (
        *EXEC_UV,
        "uv",
        "run",
        "--python",
        "/opt/fides/bin/python",
        "pytest",
        *pytest_config.args,
        test_dir,
        *_split_args(),
        *extra_args,
    )
    session.run(*run_command, external=True)


def pytest_api(session: Session, pytest_config: PytestConfig) -> None:
    """Runs tests under tests/api/."""
    _run_pytest(session, pytest_config, "tests/api/")


def pytest_cli(session: Session, pytest_config: PytestConfig) -> None:
    """Runs CLI tests under tests/cli/."""
    import copy

    session.notify("teardown")
    session.run(*START_APP, external=True)
    session.run(*LOGIN, external=True)
    local_pytest_config = copy.copy(pytest_config)
    local_pytest_config.xdist_config.parallel_runners = "0"
    run_command = (
        *EXEC_UV,
        "uv",
        "run",
        "--python",
        "/opt/fides/bin/python",
        "pytest",
        *local_pytest_config.args,
        "tests/cli/",
        *_split_args(),
    )
    session.run(*run_command, external=True)


def pytest_common(session: Session, pytest_config: PytestConfig) -> None:
    """Runs common utility tests under tests/common/."""
    _run_pytest(session, pytest_config, "tests/common/")


def pytest_config(session: Session, pytest_config: PytestConfig) -> None:
    """Runs config tests under tests/config/."""
    import copy

    session.notify("teardown")
    session.run(*START_APP, external=True)
    local_pytest_config = copy.copy(pytest_config)
    local_pytest_config.xdist_config.parallel_runners = "0"
    run_command = (
        *EXEC_UV,
        "uv",
        "run",
        "--python",
        "/opt/fides/bin/python",
        "pytest",
        *local_pytest_config.args,
        "tests/config/",
        "-m",
        "unit",
        "--full-trace",
        *_split_args(),
    )
    session.run(*run_command, external=True)


def pytest_connectors(session: Session, pytest_config: PytestConfig) -> None:
    """Runs connector tests under tests/connectors/."""
    _run_pytest(
        session,
        pytest_config,
        "tests/connectors/",
        ("-m", "not external"),
    )


def pytest_migration(session: Session, pytest_config: PytestConfig) -> None:
    """Runs database migration tests under tests/migration/."""
    _run_pytest(session, pytest_config, "tests/migration/")


def pytest_service(session: Session, pytest_config: PytestConfig) -> None:
    """Runs service tests under tests/service/."""
    _run_pytest(session, pytest_config, "tests/service/")
