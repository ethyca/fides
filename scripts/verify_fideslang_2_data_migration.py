"""
This script is designed to help with testing the Data Migration script
for moving users to Fideslang 2.0, found in Fides release 2.20

The steps to run the script are as follows:
1. In a terminal, run `nox -s teardown -- volumes ; nox -s dev` to get the server running
2. In a separate terminal, run `nox -s shell`, and then `fides user login ; fides push ; python scripts/verify_fideslang_2_data_migration.py`
3. You can run `python scripts/verify_fideslang_2_data_migration.py` as many times as needed for testing

"""
import fideslang
from fides.config import CONFIG
from fides.api.db.database import get_alembic_config
from alembic import command
from fides.core.push import push

assert (
    fideslang.__version__.split(".")[0] == "2"
), "Must have at least Fideslang version 2!"

# Test updating Datasets, including deeply nested ones
old_dataset = fideslang.models.Dataset(
    fides_key="old_dataset",
    data_categories=["user.observed"],  # new key = user.behavior
    collections=[
        fideslang.models.DatasetCollection(
            name="old_dataset_collection",
            data_categories=["user.observed"],  # new key = user.behavior
            fields=[
                fideslang.models.DatasetField(
                    name="old_dataset_field",
                    data_categories=["user.observed"],  # new key = user.behavior
                    retention=None,
                    fields=None,
                )
            ],
        )
    ],
)

# Test Privacy Declarations and Egress/Ingress updates
old_system = fideslang.models.System(
    fides_key="old_system",
    system_type="service",
    privacy_declarations=[
        fideslang.models.PrivacyDeclaration(
            name="old_privacy_declaration_1",
            data_categories=["user.observed"],  # new key = user.behavior
            data_subjects=["employee"],
            data_use="improve.system",  # new key = function.service.improve
        ),
    ],
    ingress=[
        fideslang.models.DataFlow(
            fides_key="privacy_annotations",
            type="system",
            data_categories=["user.observed"],  # new key = user.behavior
        )
    ],
    egress=[
        fideslang.models.DataFlow(
            type="system",
            fides_key="privacy_annotations",
            data_categories=["user.observed"],  # new key = user.behavior
        )
    ],
    dataset_references=["old_dataset"],
)

# This needs to exist for testing, since we can't switch back and
# forth between fideslang versions on the fly in a test script
fideslang_1_category = fideslang.models.DataCategory(
    fides_key="user.observed", parent_key="user"
)
# This needs to exist for testing, since we can't switch back and
# forth between fideslang versions on the fly in a test script
fideslang_1_use = fideslang.models.DataUse(
    fides_key="improve.system", parent_key="improve"
)

# This is used to test what happens to Taxonomy items that extended off of now-updated default items
orphaned_data_category = fideslang.models.DataCategory(
    fides_key="user.observed.custom", parent_key="user.observed"
)
# This is used to test updating Policy Rules
old_policy = fideslang.models.Policy(
    fides_key="old_policy",
    rules=[
        fideslang.models.PolicyRule(
            name="old_policy_rule",
            data_subjects=fideslang.models.PrivacyRule(
                matches=fideslang.models.MatchesEnum.ALL, values=["employee"]
            ),
            data_uses=fideslang.models.PrivacyRule(
                matches=fideslang.models.MatchesEnum.ALL,
                values=["improve.system"],  # new key = function.service.improve
            ),
            data_categories=fideslang.models.PrivacyRule(
                matches=fideslang.models.MatchesEnum.ALL,
                values=["user.observed"],  # new key = user.behavior
            ),
        )
    ],
)


def main() -> None:
    """
    Good luck :D
    """
    print("> Running Fideslang 2.0 Data Migration Test Script...")

    # Populate some variables
    fides_config = CONFIG
    database_url = fides_config.database.sync_database_uri
    auth_header = CONFIG.user.auth_header
    server_url = CONFIG.cli.server_url
    alembic_config = get_alembic_config(database_url)

    down_revision = "708a780b01ba"
    print(f"> Rolling back one migration to: {down_revision}")
    command.downgrade(alembic_config, down_revision)

    # Seed the database with objects we know will change
    print("> Seeding the database with 'outdated' Taxonomy objects")
    taxonomy = fideslang.models.Taxonomy(
        dataset=[old_dataset],
        system=[old_system],
        policy=[old_policy],
        data_category=[orphaned_data_category, fideslang_1_category],
        data_use=[fideslang_1_use],
    )
    push(url=server_url, headers=auth_header, taxonomy=taxonomy)

    # Migrate to HEAD
    print("Upgrading database to migration revision: head")
    command.upgrade(alembic_config, "head")

    # Verify that the expected changes happened to our objects


if __name__ == "__main__":
    main()
