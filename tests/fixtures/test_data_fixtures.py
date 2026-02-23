import copy
import os

import pytest
import yaml
from fideslang import DEFAULT_TAXONOMY, models
from sqlalchemy.orm import Session

from fides.api.db.crud import create_resource
from fides.api.db.database import seed_db
from fides.api.db.seed import load_default_organization, load_default_taxonomy
from fides.api.db.system import create_system
from fides.api.models.sql_models import DataCategory as DataCategoryDbModel
from fides.api.models.sql_models import DataUse, sql_model_map
from fides.api.util.cache import get_cache


@pytest.fixture
def resources_dict():
    """
    Yields a resource containing sample representations of different
    Fides resources.
    """
    resources_dict = {
        "data_category": models.DataCategory(
            organization_fides_key="1",
            fides_key="user.custom",
            parent_key="user",
            name="User dot Custom Data Category",
            description="Custom Data Category",
        ),
        "dataset": models.Dataset(
            organization_fides_key="1",
            fides_key="test_sample_db_dataset",
            name="Sample DB Dataset",
            description="This is a Sample Database Dataset",
            collections=[
                models.DatasetCollection(
                    name="user",
                    fields=[
                        models.DatasetField(
                            name="Food_Preference",
                            description="User's favorite food",
                            path="some.path",
                        ),
                        models.DatasetField(
                            name="First_Name",
                            description="A First Name Field",
                            path="another.path",
                            data_categories=["user.name"],
                        ),
                        models.DatasetField(
                            name="Email",
                            description="User's Email",
                            path="another.another.path",
                            data_categories=["user.contact.email"],
                        ),
                        models.DatasetField(
                            name="address",
                            description="example top level field for nesting",
                            path="table.address",
                            data_categories=["user.contact.address"],
                            fields=[
                                models.DatasetField(
                                    name="city",
                                    description="example city field",
                                    path="table.address.city",
                                    data_categories=["user.contact.address.city"],
                                ),
                                models.DatasetField(
                                    name="state",
                                    description="example state field",
                                    path="table.address.state",
                                    data_categories=["user.contact.address.state"],
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
        "data_subject": models.DataSubject(
            organization_fides_key="1",
            fides_key="custom_subject",
            name="Custom Data Subject",
            description="Custom Data Subject",
        ),
        "data_use": models.DataUse(
            organization_fides_key="1",
            fides_key="custom_data_use",
            name="Custom Data Use",
            description="Custom Data Use",
        ),
        "evaluation": models.Evaluation(
            fides_key="test_evaluation", status="PASS", details=["foo"], message="bar"
        ),
        "organization": models.Organization(
            fides_key="test_organization",
            name="Test Organization",
            description="Test Organization",
        ),
        "policy": models.Policy(
            organization_fides_key="1",
            fides_key="test_policy",
            name="Test Policy",
            version="1.3",
            description="Test Policy",
            rules=[],
        ),
        "policy_rule": models.PolicyRule(
            name="Test Policy",
            data_categories=models.PrivacyRule(matches="NONE", values=[]),
            data_uses=models.PrivacyRule(matches="NONE", values=["essential.service"]),
            data_subjects=models.PrivacyRule(matches="ANY", values=[]),
        ),
        "system": models.System(
            organization_fides_key="1",
            fides_key="test_system",
            system_type="SYSTEM",
            name="Test System",
            description="Test Policy",
            cookies=[],
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="essential",
                    data_subjects=[],
                    dataset_references=[],
                    cookies=[],
                )
            ],
        ),
    }
    yield resources_dict


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def fideslang_resources(
    async_session,
    resources_dict,
    default_organization,
    default_taxonomy,
    config,
):
    """
    Loads all resources from resources_dict into the database.
    This fixture runs automatically before each test function.
    """

    # Load each resource into the database
    resources = copy.deepcopy(resources_dict)
    for resource_type, resource in resources.items():
        if resource_type in sql_model_map:
            if resource_type == "system":
                await create_system(
                    resource, async_session, config.security.oauth_root_client_id
                )
            else:
                await create_resource(
                    sql_model_map[resource_type],
                    resource.model_dump(mode="json"),
                    async_session,
                )


@pytest.fixture
def test_manifests():
    test_manifests = {
        "manifest_1": {
            "dataset": [
                {
                    "name": "Test Dataset 1",
                    "organization_fides_key": 1,
                    "datasetType": {},
                    "datasetLocation": "somedb:3306",
                    "description": "Test Dataset 1",
                    "fides_key": "some_dataset",
                    "datasetTables": [],
                }
            ],
            "system": [
                {
                    "name": "Test System 1",
                    "organization_fides_key": 1,
                    "systemType": "mysql",
                    "description": "Test System 1",
                    "fides_key": "some_system",
                }
            ],
        },
        "manifest_2": {
            "dataset": [
                {
                    "name": "Test Dataset 2",
                    "description": "Test Dataset 2",
                    "organization_fides_key": 1,
                    "datasetType": {},
                    "datasetLocation": "somedb:3306",
                    "fides_key": "another_dataset",
                    "datasetTables": [],
                }
            ],
            "system": [
                {
                    "name": "Test System 2",
                    "organization_fides_key": 1,
                    "systemType": "mysql",
                    "description": "Test System 2",
                    "fides_key": "another_system",
                }
            ],
        },
    }
    yield test_manifests


@pytest.fixture
def populated_manifest_dir(test_manifests, tmp_path):
    manifest_dir = f"{tmp_path}/populated_manifest"
    os.mkdir(manifest_dir)
    for manifest in test_manifests.keys():
        with open(f"{manifest_dir}/{manifest}.yml", "w") as manifest_file:
            yaml.dump(test_manifests[manifest], manifest_file)
    return manifest_dir


@pytest.fixture
def populated_nested_manifest_dir(test_manifests, tmp_path):
    manifest_dir = f"{tmp_path}/populated_nested_manifest"
    os.mkdir(manifest_dir)
    for manifest in test_manifests.keys():
        nested_manifest_dir = f"{manifest_dir}/{manifest}"
        os.mkdir(nested_manifest_dir)
        with open(f"{nested_manifest_dir}/{manifest}.yml", "w") as manifest_file:
            yaml.dump(test_manifests[manifest], manifest_file)
    return manifest_dir


@pytest.fixture(scope="session")
def cache():
    yield get_cache()


@pytest.mark.asyncio
@pytest.fixture(scope="function")
def seed_data(db: Session):
    """
    Fixture to load default resources into the database before a test.
    """
    seed_db(db)


@pytest.fixture(scope="function")
def default_data_categories(db: Session):
    for data_category in DEFAULT_TAXONOMY.data_category:
        if (
            DataCategoryDbModel.get_by(db, field="name", value=data_category.name)
            is None
        ):
            DataCategoryDbModel.create(
                db=db, data=data_category.model_dump(mode="json")
            )


@pytest.fixture(scope="function")
def default_data_uses(db: Session):
    for data_use in DEFAULT_TAXONOMY.data_use:
        if DataUse.get_by(db, field="name", value=data_use.name) is None:
            DataUse.create(db=db, data=data_use.model_dump(mode="json"))


@pytest.fixture(scope="function")
def default_organization(db: Session):
    load_default_organization(db)


@pytest.fixture(scope="function")
def default_taxonomy(db: Session):
    load_default_taxonomy(db)
