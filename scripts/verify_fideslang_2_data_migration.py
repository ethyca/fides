"""
This script is designed to help with testing the Data Migration script for moving users to Fideslang 2.0
"""
import fideslang
import fides

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

    # Roll back one migration

    # Seed the database with objects we know will change

    # Migrate to HEAD

    # Verify that the expected changes happened to our objects


if __name__ == "__main__":
    main()
