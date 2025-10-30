"""
Contains all of the logic related to the database including connections, setup, teardown, etc.
"""

import os
import subprocess
from os import path
from pathlib import Path
from typing import Literal, Optional, Tuple

from alembic import command, script
from alembic.config import Config
from alembic.runtime import migration
from loguru import logger as log
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.schema import SchemaItem
from sqlalchemy_utils.functions import create_database, database_exists
from sqlalchemy_utils.types.encrypted.encrypted_type import InvalidCiphertextError

from fides.api.db.base import Base  # type: ignore[attr-defined]
from fides.api.db.seed import load_default_resources
from fides.api.db.session import get_db_engine
from fides.api.util.errors import get_full_exception_name

DatabaseHealth = Literal["healthy", "unhealthy", "needs migration"]

# Tables to exclude from migration auto-generation (e.g., tables without SQLAlchemy models)
EXCLUDED_TABLES = {
    "privacy_preferences_current",
    "privacy_preferences_historic",
}


def include_object(
    object: SchemaItem,  # pylint: disable=redefined-builtin
    name: str,
    type_: str,
    reflected: bool,
    compare_to: SchemaItem,
) -> bool:
    """Filter out excluded tables from migration comparison and auto-generation."""
    if type_ == "table" and name in EXCLUDED_TABLES:
        return False
    return True


def get_alembic_config(database_url: str) -> Config:
    """
    Do lots of magic to make alembic work programmatically from the CLI.
    """

    migrations_dir = path.dirname(path.abspath(__file__))
    directory = path.join(migrations_dir, "../alembic/migrations")
    config = Config(path.join(migrations_dir, "../alembic/alembic.ini"))
    config.set_main_option("script_location", directory.replace("%", "%%"))
    # Avoids invalid interpolation syntax errors if % in string
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def upgrade_db(alembic_config: Config, revision: str = "head") -> None:
    """Upgrade the database to the specified migration revision."""
    log.info(f"Running database upgrade to revision {revision}")
    command.upgrade(alembic_config, revision)


def init_db(database_url: str) -> None:
    """
    Runs the migrations and creates all of the database objects.
    """
    alembic_config = get_alembic_config(database_url)
    upgrade_db(alembic_config)


def downgrade_db(alembic_config: Config, revision: str = "head") -> None:
    """Downgrade the database to the specified migration revision."""
    log.info(f"Running database downgrade to revision {revision}")
    command.downgrade(alembic_config, revision)


def migrate_db(
    database_url: str,
    revision: str = "head",
    downgrade: bool = False,
) -> None:
    """
    Runs migrations and creates database objects if needed.

    Safe to run on an existing database when upgrading Fides version.
    """
    log.info("Migrating database")
    alembic_config = get_alembic_config(database_url)
    if downgrade:
        downgrade_db(alembic_config, revision)
    else:
        upgrade_db(alembic_config, revision)


def create_db_if_not_exists(database_url: str) -> None:
    """
    Creates a database which does not exist already.
    """
    if not database_exists(database_url):
        create_database(database_url)


def reset_db(database_url: str) -> None:
    """
    Drops all tables/metadata from the database.
    """
    log.info("Resetting database...")
    engine = get_db_engine(database_uri=database_url)
    with engine.connect() as connection:
        log.info("Dropping tables...")
        Base.metadata.drop_all(connection)

        log.info("Dropping excluded tables without models...")
        for table_name in EXCLUDED_TABLES:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))

        log.info("Dropping Alembic table...")
        migration_context = migration.MigrationContext.configure(connection)
        version = migration_context._version  # pylint: disable=protected-access
        if version.exists(connection):
            version.drop(connection)
    log.info("Reset complete.")


def get_db_health(
    database_url: str, db: Session
) -> Tuple[DatabaseHealth, Optional[str]]:
    """Checks if the db is reachable and up-to-date with Alembic migrations."""
    try:
        alembic_config = get_alembic_config(database_url)
        alembic_script_directory = script.ScriptDirectory.from_config(alembic_config)
        context = migration.MigrationContext.configure(db.connection())
        current_revision = context.get_current_revision()
        if (
            context.get_current_revision()
            != alembic_script_directory.get_current_head()
        ):
            db_health: DatabaseHealth = "needs migration"
        else:
            db_health = "healthy"
        return db_health, current_revision
    except Exception as error:  # pylint: disable=broad-except
        error_type = get_full_exception_name(error)
        log.error("Unable to reach the database: {}: {}", error_type, error)
        return ("unhealthy", None)


def seed_db(session: Session) -> None:
    """Load default resources into the database"""
    load_default_resources(session)


def configure_db(database_url: str, revision: Optional[str] = "head") -> None:
    """Set up the db to be used by the app. Creates db if needed and runs migrations."""
    try:
        create_db_if_not_exists(database_url)
        migrate_db(database_url, revision=revision)  # type: ignore[arg-type]

    except InvalidCiphertextError as cipher_error:
        log.error(
            "Unable to configure database due to a decryption error! Check to ensure your `app_encryption_key` has not changed."
        )
        log.opt(exception=True).error(cipher_error)

    except Exception as error:  # pylint: disable=broad-except
        error_type = get_full_exception_name(error)
        log.error("Unable to configure database: {}: {}", error_type, error)
        log.opt(exception=True).error(error)
        raise


def check_missing_migrations(database_url: str) -> None:
    """
    Tries to autogenerate migrations, returns True if a migration
    was generated.
    """
    engine = get_db_engine(database_uri=database_url)
    connection = engine.connect()

    migration_context = migration.MigrationContext.configure(
        connection, opts={"include_object": include_object}
    )
    result = command.autogen.compare_metadata(migration_context, Base.metadata)  # type: ignore[attr-defined]

    if result:
        log.error("Migration needs to be generated!")
        log.error("Detected the following schema differences:")
        for item in result:
            log.error(f"  - {item}")
        raise SystemExit("Migration needs to be generated!")
    print("No migrations need to be generated.")


def _get_base_branch_for_comparison() -> str:
    """
    Determine the base branch to compare against for detecting new migrations.

    In GitHub Actions PRs, uses GITHUB_BASE_REF (the PR target branch).
    Otherwise, falls back to origin/main for local development.

    Returns:
        The base branch reference (e.g., 'origin/main', 'origin/develop')
    """
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        base_branch = f"origin/{base_ref}"
        log.info(f"Comparing against PR target branch: {base_branch}")
    else:
        base_branch = "origin/main"
        log.info(f"No GITHUB_BASE_REF found, comparing against: {base_branch}")
    return base_branch


def _get_new_migration_files(repo_root: str, base_branch: str) -> list[str]:
    """
    Get list of new migration files added in the current branch.

    Files are sorted by the timestamp in their filename to ensure chronological order.
    Migration files follow the pattern: xx_YYYY_MM_DD_HHMM_revision_description.py

    Args:
        repo_root: Absolute path to the git repository root
        base_branch: The base branch to compare against

    Returns:
        List of relative file paths to new migration files, sorted chronologically

    Raises:
        SystemExit: If the migrations directory does not exist
    """
    # Validate that the migrations directory exists
    migrations_dir = (
        Path(repo_root)
        / "src"
        / "fides"
        / "api"
        / "alembic"
        / "migrations"
        / "versions"
    )
    if not migrations_dir.exists():
        log.error(f"Migrations directory not found: {migrations_dir}")
        raise SystemExit(
            f"Migration directory not found at expected path: {migrations_dir}\n"
            "If the migrations directory has been moved, update the path in "
            "fides.api.db.database._get_new_migration_files()"
        )

    migration_pattern = "src/fides/api/alembic/migrations/versions/*.py"
    diff_output = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=A",  # Only added files
            f"{base_branch}...HEAD",
            "--",
            migration_pattern,
        ],
        stderr=subprocess.STDOUT,
        text=True,
        cwd=repo_root,
    ).strip()

    if not diff_output:
        return []

    migration_files = [f for f in diff_output.split("\n") if f]

    # Sort by filename to ensure chronological order
    # Files are named: xx_YYYY_MM_DD_HHMM_revision_description.py
    # Sorting alphabetically will sort them chronologically due to the date format
    migration_files.sort()

    return migration_files


def _parse_migration_revisions(migration_path: Path) -> tuple[str, Optional[str]]:
    """
    Extract revision and down_revision IDs from a migration file.

    Args:
        migration_path: Path to the migration file

    Returns:
        Tuple of (revision, down_revision). down_revision may be None.

    Raises:
        SystemExit: If revision ID cannot be found in the file
    """
    revision = None
    down_revision = None

    with open(migration_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("revision ="):
                revision = line.split("=")[1].strip().strip("\"'")
            elif line.strip().startswith("down_revision ="):
                down_rev_value = line.split("=")[1].strip().strip("\"'")
                if down_rev_value.lower() != "none":
                    down_revision = down_rev_value

    if not revision:
        log.error(f"Could not find revision ID in {migration_path}")
        raise SystemExit(f"Invalid migration file: {migration_path}")

    return revision, down_revision


def _test_migrations_upgrade_downgrade_sequence(
    alembic_config: Config,
    migrations: list[tuple[str, str, Optional[str]]],
) -> None:
    """
    Test multiple migrations can be upgraded and downgraded successfully in sequence.

    Tests all new migrations together by:
    1. Downgrading incrementally through all migrations (newest to oldest)
    2. Upgrading incrementally back through all migrations (oldest to newest)

    After Phase 2, the database is at the newest migration revision, which should
    match HEAD for the new migrations being tested.

    This approach tests migrations in a realistic sequence and can catch
    interaction issues between migrations.

    Args:
        alembic_config: Alembic configuration
        migrations: List of (migration_name, revision, down_revision) tuples

    Raises:
        SystemExit: If any migration upgrade/downgrade test fails
    """
    if not migrations:
        return

    log.info(f"Testing {len(migrations)} migration(s) in sequence")

    try:
        # Phase 1: Downgrade through all migrations (newest to oldest)
        log.info("Phase 1: Downgrading through all new migrations...")
        for migration_name, revision, down_revision in reversed(migrations):
            if down_revision:
                log.info(f"  Downgrading {migration_name} to {down_revision}...")
                downgrade_db(alembic_config, down_revision)
            else:
                log.info(f"  Skipping {migration_name} (no down_revision)")

        # Phase 2: Upgrade back through all migrations (oldest to newest)
        log.info("Phase 2: Upgrading back through all new migrations...")
        for migration_name, revision, down_revision in migrations:
            log.info(f"  Upgrading {migration_name} to {revision}...")
            upgrade_db(alembic_config, revision)

        log.info(f"✓ All {len(migrations)} migration(s) passed upgrade/downgrade test")

    except Exception as error:
        log.error("Migration upgrade/downgrade sequence test failed!")
        log.error(str(error))
        raise SystemExit("Migration upgrade/downgrade test failed")


def check_new_migrations_upgrade_downgrade(database_url: str) -> None:
    """
    Detects new migrations added in the current branch and tests that they
    can be successfully upgraded and downgraded.

    Uses git to compare against the target/base branch to find new migration files.
    In CI, uses GITHUB_BASE_REF if available, otherwise falls back to origin/main.
    """
    try:
        # Get the repo root directory
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()

        # Determine base branch and get new migration files
        base_branch = _get_base_branch_for_comparison()
        migration_files = _get_new_migration_files(repo_root, base_branch)

        if not migration_files:
            log.info("No new migration files detected in current branch")
            print("No new migrations to test.")
            return

        log.info(f"Detected {len(migration_files)} new migration(s) to test")

        # Log the migrations in order
        for i, file_path in enumerate(migration_files, 1):
            log.info(f"  {i}. {Path(file_path).name}")

        alembic_config = get_alembic_config(database_url)

        # Parse all migrations first
        migrations = []
        for file_path in migration_files:
            abs_path = Path(repo_root) / file_path
            revision, down_revision = _parse_migration_revisions(abs_path)
            migrations.append((abs_path.name, revision, down_revision))

        # Test all migrations in sequence
        _test_migrations_upgrade_downgrade_sequence(alembic_config, migrations)

        print(
            f"All {len(migration_files)} new migration(s) passed upgrade/downgrade tests."
        )

    except subprocess.CalledProcessError as error:
        # Git command failed - might not be in a git repo or no origin/main
        log.warning(f"Could not detect new migrations via git: {error}")
        print("Skipping migration upgrade/downgrade check (git detection failed).")
