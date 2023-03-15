# pylint: disable=missing-docstring, redefined-outer-name
from typing import Any

import pytest
from fideslang import models
from starlette.testclient import TestClient

from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.sql_models import (  # type: ignore[attr-defined]
    CustomField,
    CustomFieldDefinition,
    System,
)
from fides.api.ops.util.data_category import DataCategory
from fides.core.config import FidesConfig

HEADERS_ROW_RESPONSE_PAYLOAD = {
    "dataset.name": "Fides Dataset",
    "system.name": "Fides System",
    "system.administrating_department": "Department or Business Function",
    "system.privacy_declaration.data_use.name": "Purpose of Processing",
    "system.joint_controller": "Joint Controller",
    "system.privacy_declaration.data_subjects.name": "Categories of Individuals",
    "unioned_data_categories": "Categories of Personal Data (Fides Taxonomy)",
    "system.privacy_declaration.data_use.recipients": "Categories of Recipients",
    "system.link_to_processor_contract": "Link to Contract with Processor",
    "third_country_combined": "Third Country Transfers",
    "system.third_country_safeguards": "Safeguards for Exceptional Transfers of Personal Data",
    "dataset.retention": "Retention Schedule",
    "organization.link_to_security_policy": "General Description of Security Measures",
    "system.data_responsibility_title": "Role or Responsibility",
    "system.privacy_declaration.data_use.legal_basis": "Article 6 lawful basis for processing personal data",
    "system.privacy_declaration.data_use.special_category": "Article 9 condition for processing special category data",
    "system.privacy_declaration.data_use.legitimate_interest": "Legitimate interests for the processing (if applicable)",
    "system.privacy_declaration.data_use.legitimate_interest_impact_assessment": "Link to record of legitimate interests assessment (if applicable)",
    "system.privacy_declaration.data_subjects.rights_available": "Rights available to individuals",
    "system.privacy_declaration.data_subjects.automated_decisions_or_profiling": "Existence of automated decision-making, including profiling (if applicable)",
    "dataset.source_name": "The source of the personal data (if applicable)",
    "system.data_protection_impact_assessment.is_required": "Data Protection Impact Assessment required?",
    "system.data_protection_impact_assessment.progress": "Data Protection Impact Assessment progress",
    "system.data_protection_impact_assessment.link": "Link to Data Protection Impact Assessment",
    "system.fides_key": "System Fides Key",
    "dataset.fides_key": "Dataset Fides Key (if applicable)",
    "system.system_dependencies": "Related cross-system dependencies",
    "system.description": "Description of the System",
    "system.ingress": "Related Systems which receive data to this System",
    "system.egress": "Related Systems which send data to this System",
}

HEADERS_ROW_SINGLE_CUSTOM_FIELD = HEADERS_ROW_RESPONSE_PAYLOAD.copy()
HEADERS_ROW_SINGLE_CUSTOM_FIELD.update({"system.country": "country"})
HEADERS_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL = HEADERS_ROW_RESPONSE_PAYLOAD.copy()
HEADERS_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL.update(
    {"system.country_multival": "country_multival"}
)
HEADERS_ROW_TWO_CUSTOM_FIELDS = HEADERS_ROW_SINGLE_CUSTOM_FIELD.copy()
HEADERS_ROW_TWO_CUSTOM_FIELDS.update({"system.owner": "owner"})
HEADERS_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL = (
    HEADERS_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL.copy()
)
HEADERS_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL.update({"system.owner": "owner"})


NO_PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD = {
    "dataset.name": "N/A",
    "system.name": "Test System",
    "system.administrating_department": "Not defined",
    "system.privacy_declaration.data_use.name": "N/A",
    "system.joint_controller": "",
    "system.privacy_declaration.data_subjects.name": "N/A",
    "unioned_data_categories": "N/A",
    "system.privacy_declaration.data_use.recipients": "N/A",
    "system.link_to_processor_contract": "",
    "third_country_combined": "N/A",
    "system.third_country_safeguards": "",
    "dataset.retention": "N/A",
    "organization.link_to_security_policy": "",
    "system.data_responsibility_title": "Controller",
    "system.privacy_declaration.data_use.legal_basis": "N/A",
    "system.privacy_declaration.data_use.special_category": "N/A",
    "system.privacy_declaration.data_use.legitimate_interest": "N/A",
    "system.privacy_declaration.data_use.legitimate_interest_impact_assessment": "N/A",
    "system.privacy_declaration.data_subjects.rights_available": "N/A",
    "system.privacy_declaration.data_subjects.automated_decisions_or_profiling": "N/A",
    "dataset.source_name": "N/A",
    "system.data_protection_impact_assessment.is_required": False,
    "system.data_protection_impact_assessment.progress": "N/A",
    "system.data_protection_impact_assessment.link": "N/A",
    "system.fides_key": "test_system",
    "dataset.fides_key": "N/A",
    "system.system_dependencies": "",
    "system.description": "Test Policy",
    "system.ingress": "",
    "system.egress": "",
}

NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD = (
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD.copy()
)
NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD.update({"system.country": "usa"})
NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL = (
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD.copy()
)
NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL.update(
    {"system.country_multival": "usa, canada"}
)
NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_NO_VALUE = (
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD.copy()
)
NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_NO_VALUE.update(
    {"system.country": "N/A"}
)
NO_PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS = (
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD.copy()
)
NO_PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS.update({"system.owner": "John"})
NO_PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL = (
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL.copy()
)
NO_PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL.update(
    {"system.owner": "John"}
)

PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD = {
    "dataset.name": "N/A",
    "system.name": "Test System 2",
    "system.administrating_department": "Not defined",
    "system.privacy_declaration.data_use.name": "Provide the capability",
    "system.joint_controller": "",
    "system.privacy_declaration.data_subjects.name": "Customer",
    "unioned_data_categories": "user",
    "system.privacy_declaration.data_use.recipients": "N/A",
    "system.link_to_processor_contract": "",
    "third_country_combined": "N/A",
    "system.third_country_safeguards": "",
    "dataset.retention": "N/A",
    "organization.link_to_security_policy": "",
    "system.data_responsibility_title": "Controller",
    "system.privacy_declaration.data_use.legal_basis": "N/A",
    "system.privacy_declaration.data_use.special_category": "N/A",
    "system.privacy_declaration.data_use.legitimate_interest": "N/A",
    "system.privacy_declaration.data_use.legitimate_interest_impact_assessment": "N/A",
    "system.privacy_declaration.data_subjects.rights_available": "No data subject rights listed",
    "system.privacy_declaration.data_subjects.automated_decisions_or_profiling": "N/A",
    "dataset.source_name": "N/A",
    "system.data_protection_impact_assessment.is_required": False,
    "system.data_protection_impact_assessment.progress": "N/A",
    "system.data_protection_impact_assessment.link": "N/A",
    "system.fides_key": "test_system_2",
    "dataset.fides_key": "N/A",
    "system.system_dependencies": "",
    "system.description": "Test Policy 2",
    "system.ingress": "",
    "system.egress": "",
}

PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD = (
    PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD.copy()
)
PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD.update({"system.country": "canada"})
PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL = (
    PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD.copy()
)
PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL.update(
    {"system.country_multival": "usa, canada"}
)
PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_NO_VALUE = (
    PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD.copy()
)
PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_NO_VALUE.update(
    {"system.country": "N/A"}
)
PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS = (
    PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD.copy()
)
PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS.update({"system.owner": "Jane"})

PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL = (
    PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL.copy()
)
PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL.update(
    {"system.owner": "Jane"}
)

### Expected Responses

EXPECTED_RESPONSE_NO_CUSTOM_FIELDS_NO_PRIVACY_DECLARATION = [
    HEADERS_ROW_RESPONSE_PAYLOAD,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD,
]

EXPECTED_RESPONSE_NO_CUSTOM_FIELDS_PRIVACY_DECLARATION = [
    HEADERS_ROW_RESPONSE_PAYLOAD,
    PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD,
]

EXPECTED_RESPONSE_NO_CUSTOM_FIELDS_TWO_SYSTEMS = [
    HEADERS_ROW_RESPONSE_PAYLOAD,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD,
    PRIVACY_DECLARATION_SYSTEM_ROW_RESPONSE_PAYLOAD,
]

EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELDS_NO_VALUE_NO_PRIVACY_DECLARATION = [
    HEADERS_ROW_RESPONSE_PAYLOAD,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_NO_VALUE,
]

EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_NO_VALUE_PRIVACY_DECLARATION = [
    HEADERS_ROW_RESPONSE_PAYLOAD,
    PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_NO_VALUE,
]

EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_NO_PRIVACY_DECLARATION = [
    HEADERS_ROW_SINGLE_CUSTOM_FIELD,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD,
]

EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_MULTIVAL_NO_PRIVACY_DECLARATION = [
    HEADERS_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL,
]

EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_PRIVACY_DECLARATION = [
    HEADERS_ROW_SINGLE_CUSTOM_FIELD,
    PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD,
]

EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_MULTIVAL_PRIVACY_DECLARATION = [
    HEADERS_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL,
    PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL,
]

EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_TWO_SYSTEMS = [
    HEADERS_ROW_SINGLE_CUSTOM_FIELD,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD,
    PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD,
]

EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_MULTIVAL_TWO_SYSTEMS = [
    HEADERS_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL,
    PRIVACY_DECLARATION_SYSTEM_ROW_SINGLE_CUSTOM_FIELD_MULTIVAL,
]

EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_NO_PRIVACY_DECLARATION = [
    HEADERS_ROW_TWO_CUSTOM_FIELDS,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS,
]

EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_ONE_MULTIVAL_NO_PRIVACY_DECLARATION = [
    HEADERS_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL,
]

EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_PRIVACY_DECLARATION = [
    HEADERS_ROW_TWO_CUSTOM_FIELDS,
    PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS,
]

EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_ONE_MULTIVAL_PRIVACY_DECLARATION = [
    HEADERS_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL,
    PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL,
]

EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_TWO_SYSTEMS = [
    HEADERS_ROW_TWO_CUSTOM_FIELDS,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS,
    PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS,
]

EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_ONE_MULTIVAL_TWO_SYSTEMS = [
    HEADERS_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL,
    NO_PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL,
    PRIVACY_DECLARATION_SYSTEM_ROW_TWO_CUSTOM_FIELDS_ONE_MULTIVAL,
]


@pytest.fixture
def system_no_privacy_declarations(db):
    """
    A sample system with no privacy declarations
    """
    system = models.System(
        organization_fides_key="default_organization",
        registryId=1,
        fides_key="test_system",
        system_type="SYSTEM",
        name="Test System",
        description="Test Policy",
        privacy_declarations=[],
        system_dependencies=[],
    )
    system_db_record = System.create_or_update(db=db, data=system.dict())
    yield system_db_record
    system_db_record.delete(db)


@pytest.fixture
def system_privacy_declarations(db):
    """
    A sample system with privacy declarations
    """
    system = models.System(
        organization_fides_key="default_organization",
        registryId=2,
        fides_key="test_system_2",
        system_type="SYSTEM",
        name="Test System 2",
        description="Test Policy 2",
        privacy_declarations=[
            models.PrivacyDeclaration(
                name="declaration-name-2",
                data_categories=[DataCategory("user").value],
                data_use="provide",
                data_subjects=["customer"],
                data_qualifier="aggregated_data",
                dataset_references=[],
            )
        ],
        system_dependencies=[],
    )
    system_db_record = System.create_or_update(db=db, data=system.dict())
    yield system_db_record
    system_db_record.delete(db)


@pytest.fixture
def country_field_definition(db):
    country_definition = CustomFieldDefinition.create_or_update(
        db=db,
        data={
            "name": "country",
            "description": "test",
            "field_type": "string",
            "resource_type": "system",
            "field_definition": "string",
        },
    )
    yield country_definition
    country_definition.delete(db)


@pytest.fixture
def country_multival_field_definition(db):
    country_definition = CustomFieldDefinition.create_or_update(
        db=db,
        data={
            "name": "country_multival",
            "description": "country field but multiple values allowed",
            "field_type": "string[]",
            "resource_type": "system",
            "field_definition": "string",
        },
    )
    yield country_definition
    country_definition.delete(db)


@pytest.fixture
def owner_field_definition(db):
    owner_definition = CustomFieldDefinition.create_or_update(
        db=db,
        data={
            "name": "owner",
            "description": "test",
            "field_type": "string",
            "resource_type": "system",
            "field_definition": "string",
        },
    )
    yield owner_definition
    owner_definition.delete(db)


@pytest.fixture
def country_field_instance_no_privacy_declarations(
    db,
    country_field_definition: CustomFieldDefinition,
    system_no_privacy_declarations: System,
):
    country_instance = CustomField.create(
        db=db,
        data={
            "resource_type": country_field_definition.resource_type,
            "resource_id": system_no_privacy_declarations.fides_key,
            "custom_field_definition_id": country_field_definition.id,
            "value": ["usa"],
        },
    )
    yield country_instance
    country_instance.delete(db)


@pytest.fixture
def country_multival_field_instance_no_privacy_declarations(
    db,
    country_multival_field_definition: CustomFieldDefinition,
    system_no_privacy_declarations: System,
):
    country_instance = CustomField.create(
        db=db,
        data={
            "resource_type": country_multival_field_definition.resource_type,
            "resource_id": system_no_privacy_declarations.fides_key,
            "custom_field_definition_id": country_multival_field_definition.id,
            "value": ["usa", "canada"],
        },
    )
    yield country_instance
    country_instance.delete(db)


@pytest.fixture
def country_field_instance_privacy_declarations(
    db,
    country_field_definition: CustomFieldDefinition,
    system_privacy_declarations: System,
):
    country_instance = CustomField.create(
        db=db,
        data={
            "resource_type": country_field_definition.resource_type,
            "resource_id": system_privacy_declarations.fides_key,
            "custom_field_definition_id": country_field_definition.id,
            "value": ["canada"],
        },
    )
    yield country_instance
    country_instance.delete(db)


@pytest.fixture
def country_multival_field_instance_privacy_declarations(
    db,
    country_multival_field_definition: CustomFieldDefinition,
    system_privacy_declarations: System,
):
    country_instance = CustomField.create(
        db=db,
        data={
            "resource_type": country_multival_field_definition.resource_type,
            "resource_id": system_privacy_declarations.fides_key,
            "custom_field_definition_id": country_multival_field_definition.id,
            "value": ["usa", "canada"],
        },
    )
    yield country_instance
    country_instance.delete(db)


@pytest.fixture
def owner_field_instance_no_privacy_declarations(
    db,
    owner_field_definition: CustomFieldDefinition,
    system_no_privacy_declarations: System,
):
    owner_instance = CustomField.create(
        db=db,
        data={
            "resource_type": owner_field_definition.resource_type,
            "resource_id": system_no_privacy_declarations.fides_key,
            "custom_field_definition_id": owner_field_definition.id,
            "value": ["John"],
        },
    )
    yield owner_instance
    owner_instance.delete(db)


@pytest.fixture
def owner_field_instance_privacy_declarations(
    db,
    owner_field_definition: CustomFieldDefinition,
    system_privacy_declarations: System,
):
    owner_instance = CustomField.create(
        db=db,
        data={
            "resource_type": owner_field_definition.resource_type,
            "resource_id": system_privacy_declarations.fides_key,
            "custom_field_definition_id": owner_field_definition.id,
            "value": ["Jane"],
        },
    )
    yield owner_instance
    owner_instance.delete(db)


@pytest.mark.integration
@pytest.mark.usefixtures("system_no_privacy_declarations")
@pytest.mark.parametrize(
    "organization_fides_key, expected_status_code, expected_response_payload",
    [
        ("fake_organization", 404, None),
        (
            "default_organization",
            200,
            EXPECTED_RESPONSE_NO_CUSTOM_FIELDS_NO_PRIVACY_DECLARATION,
        ),
    ],
)
def test_datamap(
    test_config: FidesConfig,
    organization_fides_key: str,
    expected_status_code: int,
    expected_response_payload: Any,
    test_client: TestClient,
) -> None:
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + organization_fides_key,
        headers=test_config.user.auth_header,
    )
    assert response.status_code == expected_status_code
    if expected_response_payload is not None:
        assert response.json() == expected_response_payload


@pytest.mark.integration
@pytest.mark.usefixtures("system_privacy_declarations")
@pytest.mark.parametrize(
    "organization_fides_key, expected_status_code, expected_response_payload",
    [
        ("fake_organization", 404, None),
        (
            "default_organization",
            200,
            EXPECTED_RESPONSE_NO_CUSTOM_FIELDS_PRIVACY_DECLARATION,
        ),
    ],
)
def test_datamap_with_privacy_declaration(
    test_config: FidesConfig,
    organization_fides_key: str,
    expected_status_code: int,
    expected_response_payload: Any,
    test_client: TestClient,
) -> None:
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + organization_fides_key,
        headers=test_config.user.auth_header,
    )
    assert response.status_code == expected_status_code
    if expected_response_payload is not None:
        assert response.json() == expected_response_payload


@pytest.mark.integration
@pytest.mark.usefixtures(
    "system_no_privacy_declarations",
    "system_privacy_declarations",
)
@pytest.mark.parametrize(
    "organization_fides_key, expected_status_code, expected_response_payload",
    [
        ("fake_organization", 404, None),
        (
            "default_organization",
            200,
            EXPECTED_RESPONSE_NO_CUSTOM_FIELDS_TWO_SYSTEMS,
        ),
    ],
)
def test_datamap_two_systems(
    test_config: FidesConfig,
    organization_fides_key: str,
    expected_status_code: int,
    expected_response_payload: Any,
    test_client: TestClient,
) -> None:
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + organization_fides_key,
        headers=test_config.user.auth_header,
    )
    assert response.status_code == expected_status_code
    if expected_response_payload is not None:
        assert response.json() == expected_response_payload


@pytest.mark.integration
@pytest.mark.skip(
    "known issue where custom fields with no value do not show up as a column in datamap"
)
@pytest.mark.usefixtures("system_privacy_declarations", "country_field_definition")
@pytest.mark.parametrize(
    "organization_fides_key, expected_status_code, expected_response_payload",
    [
        ("fake_organization", 404, None),
        (
            "default_organization",
            200,
            EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_NO_VALUE_PRIVACY_DECLARATION,
        ),
    ],
)
def test_datamap_no_privacy_declaration_single_custom_field_no_value(
    test_config,
    organization_fides_key,
    expected_status_code,
    expected_response_payload,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + organization_fides_key,
        headers=test_config.user.auth_header,
    )
    assert response.status_code == expected_status_code
    if expected_response_payload is not None:
        assert response.json() == expected_response_payload


@pytest.mark.integration
@pytest.mark.skip(
    "known issue where custom fields with no value do not show up as a column in datamap"
)
@pytest.mark.usefixtures("system_no_privacy_declarations", "country_field_definition")
@pytest.mark.parametrize(
    "organization_fides_key, expected_status_code, expected_response_payload",
    [
        ("fake_organization", 404, None),
        (
            "default_organization",
            200,
            EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_NO_VALUE_PRIVACY_DECLARATION,
        ),
    ],
)
def test_datamap_privacy_declaration_single_custom_field_no_value(
    test_config,
    organization_fides_key,
    expected_status_code,
    expected_response_payload,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + organization_fides_key,
        headers=test_config.user.auth_header,
    )
    assert response.status_code == expected_status_code
    if expected_response_payload is not None:
        assert response.json() == expected_response_payload


@pytest.mark.integration
@pytest.mark.parametrize(
    "organization_fides_key, expected_status_code, expected_response_payload",
    [
        ("fake_organization", 404, None),
        (
            "default_organization",
            200,
            EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_NO_PRIVACY_DECLARATION,
        ),
    ],
)
@pytest.mark.usefixtures("country_field_instance_no_privacy_declarations")
def test_datamap_no_privacy_declaration_single_custom_field(
    test_config,
    organization_fides_key,
    expected_status_code,
    expected_response_payload,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + organization_fides_key,
        headers=test_config.user.auth_header,
    )
    assert response.status_code == expected_status_code
    if expected_response_payload is not None:
        assert response.json() == expected_response_payload


@pytest.mark.integration
@pytest.mark.usefixtures("country_field_instance_privacy_declarations")
def test_datamap_privacy_declaration_single_custom_field(
    test_config,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert response.json() == EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_PRIVACY_DECLARATION


@pytest.mark.integration
@pytest.mark.usefixtures("country_multival_field_instance_no_privacy_declarations")
def test_datamap_no_privacy_declaration_single_custom_field_multival(
    test_config,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert (
        response.json()
        == EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_MULTIVAL_NO_PRIVACY_DECLARATION
    )


@pytest.mark.integration
@pytest.mark.usefixtures("country_multival_field_instance_privacy_declarations")
def test_datamap_privacy_declaration_single_custom_field_multival(
    test_config,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert (
        response.json()
        == EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_MULTIVAL_PRIVACY_DECLARATION
    )


@pytest.mark.integration
@pytest.mark.usefixtures(
    "country_field_instance_no_privacy_declarations",
    "country_field_instance_privacy_declarations",
)
def test_datamap_single_custom_field_two_systems(
    test_config,
    test_client,
):
    """
    Tests expected response with two systems - one with privacy declarations, one without -
    and a single custom field populated on both systems.
    """
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert response.json() == EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_TWO_SYSTEMS


@pytest.mark.integration
@pytest.mark.usefixtures(
    "country_multival_field_instance_no_privacy_declarations",
    "country_multival_field_instance_privacy_declarations",
)
def test_datamap_single_custom_field_two_systems_multival(
    test_config,
    test_client,
):
    """
    Tests expected response with two systems - one with privacy declarations, one without -
    and a single multival custom field populated on both systems.
    """
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert response.json() == EXPECTED_RESPONSE_SINGLE_CUSTOM_FIELD_MULTIVAL_TWO_SYSTEMS


@pytest.mark.integration
@pytest.mark.usefixtures(
    "country_field_instance_no_privacy_declarations",
    "owner_field_instance_no_privacy_declarations",
)
def test_datamap_no_privacy_declaration_two_custom_fields(
    test_config,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200

    assert response.json() == EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_NO_PRIVACY_DECLARATION


@pytest.mark.integration
@pytest.mark.usefixtures(
    "country_multival_field_instance_no_privacy_declarations",
    "owner_field_instance_no_privacy_declarations",
)
def test_datamap_no_privacy_declaration_two_custom_fields_one_multival(
    test_config,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert (
        response.json()
        == EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_ONE_MULTIVAL_NO_PRIVACY_DECLARATION
    )


@pytest.mark.integration
@pytest.mark.usefixtures(
    "country_field_instance_privacy_declarations",
    "owner_field_instance_privacy_declarations",
)
def test_datamap_privacy_declarations_two_custom_fields(
    test_config,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert response.json() == EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_PRIVACY_DECLARATION


@pytest.mark.integration
@pytest.mark.usefixtures(
    "country_multival_field_instance_privacy_declarations",
    "owner_field_instance_privacy_declarations",
)
def test_datamap_privacy_declarations_two_custom_fields_one_multival(
    test_config,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert (
        response.json()
        == EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_ONE_MULTIVAL_PRIVACY_DECLARATION
    )


@pytest.mark.integration
@pytest.mark.usefixtures(
    "country_field_instance_no_privacy_declarations",
    "owner_field_instance_no_privacy_declarations",
    "country_field_instance_privacy_declarations",
    "owner_field_instance_privacy_declarations",
)
def test_datamap_two_custom_fields_two_systems(
    test_config,
    test_client,
):
    """
    Tests expected response with two systems - one with privacy declarations, one without -
    and two custom fields populated on both systems.
    """
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert response.json() == EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_TWO_SYSTEMS


@pytest.mark.integration
@pytest.mark.usefixtures(
    "country_multival_field_instance_no_privacy_declarations",
    "owner_field_instance_no_privacy_declarations",
    "country_multival_field_instance_privacy_declarations",
    "owner_field_instance_privacy_declarations",
)
def test_datamap_two_custom_fields_one_multival_two_systems(
    test_config,
    test_client,
):
    """
    Tests expected response with two systems - one with privacy declarations, one without -
    and two custom fields, one multival, populated on both systems.
    """
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + "default_organization",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert (
        response.json() == EXPECTED_RESPONSE_TWO_CUSTOM_FIELDS_ONE_MULTIVAL_TWO_SYSTEMS
    )
