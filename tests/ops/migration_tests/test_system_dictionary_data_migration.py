from fides.api.alembic.migrations.versions.fd52d5f08c17_system_dictionary_data_migration import (
    _flatten_data_protection_impact_assessment,
    _get_privacy_declaration_legal_basis_for_processing,
    _get_retention_period,
    _get_third_party_data,
    _system_calculate_does_international_transfers,
    _system_transform_data_responsibility_title_type,
    _system_transform_joint_controller_info,
)


class TestSystemDictionaryDataMigrationFunctions:
    """Test functions used in the alembic data migration for systems and privacy declaration fields"""

    def test_system_transform_joint_controller_info(self):
        joint_controller_info = _system_transform_joint_controller_info(
            joint_controller_decrypted={}, datasets_joint_controller_decrypted=[{}]
        )
        assert joint_controller_info is None

        joint_controller_info = _system_transform_joint_controller_info(
            joint_controller_decrypted={"address": "233 Test Town"},
            datasets_joint_controller_decrypted=[],
        )
        assert joint_controller_info == "233 Test Town"

        joint_controller_info = _system_transform_joint_controller_info(
            joint_controller_decrypted={"name": "Jane Doe", "address": "233 Test Town"},
            datasets_joint_controller_decrypted=[{}],
        )
        assert joint_controller_info == "Jane Doe; 233 Test Town"

        joint_controller_info = _system_transform_joint_controller_info(
            joint_controller_decrypted={
                "name": "Jane Doe",
                "address": "233 Test Town",
                "email": "jane@example.com",
            },
            datasets_joint_controller_decrypted=[{}],
        )
        assert joint_controller_info == "Jane Doe; 233 Test Town; jane@example.com"

        joint_controller_info = _system_transform_joint_controller_info(
            joint_controller_decrypted={
                "name": "N/A",
                "address": "N/A",
                "email": "N/A",
                "phone": "N/A",
            },
            datasets_joint_controller_decrypted=[{}],
        )
        assert joint_controller_info is None

        joint_controller_info = _system_transform_joint_controller_info(
            joint_controller_decrypted={
                "name": "Jane Doe",
                "address": "233 Test Town",
                "email": "jane@example.com",
                "phone": "224-242-2424",
            },
            datasets_joint_controller_decrypted=[{}],
        )
        assert (
            joint_controller_info
            == "Jane Doe; 233 Test Town; jane@example.com; 224-242-2424"
        )

        joint_controller_info = _system_transform_joint_controller_info(
            joint_controller_decrypted=None,
            datasets_joint_controller_decrypted=[
                None,
                {
                    "name": "Jane Doe",
                    "address": "233 Test Town",
                    "email": "jane@example.com",
                    "phone": "224-242-2424",
                },
            ],
        )
        assert (
            joint_controller_info
            == "Jane Doe; 233 Test Town; jane@example.com; 224-242-2424"
        )

    def test_system_calculate_does_international_transfers(self):
        assert (
            _system_calculate_does_international_transfers(
                system_third_country_transfers=["GBR"],
                dataset_third_country_transfers=["IRL", "GBR"],
            )
            is True
        )

        assert (
            _system_calculate_does_international_transfers(
                system_third_country_transfers=None,
                dataset_third_country_transfers=None,
            )
            is False
        )

        assert (
            _system_calculate_does_international_transfers(
                system_third_country_transfers=[],
                dataset_third_country_transfers=["GBR"],
            )
            is True
        )

    def test_system_transform_data_responsibility_title_type(self):
        assert _system_transform_data_responsibility_title_type(dept_str=None) == []

        assert _system_transform_data_responsibility_title_type(dept_str="") == []

        assert _system_transform_data_responsibility_title_type(
            dept_str="Controller"
        ) == ["Controller"]

    def test_flatten_data_protection_impact_assessment(self):
        assert _flatten_data_protection_impact_assessment(
            data_protection_impact_assessment=None
        ) == (False, None, None)

        assert _flatten_data_protection_impact_assessment(
            data_protection_impact_assessment=[]
        ) == (False, None, None)

        assert _flatten_data_protection_impact_assessment(
            data_protection_impact_assessment={}
        ) == (False, None, None)

        assert _flatten_data_protection_impact_assessment(
            data_protection_impact_assessment={"is_required": True}
        ) == (True, None, None)

        assert _flatten_data_protection_impact_assessment(
            data_protection_impact_assessment={
                "is_required": True,
                "progress": "pending",
                "link": "www.example.com/dpa",
            }
        ) == (True, "pending", "www.example.com/dpa")

    def test_get_privacy_declaration_legal_basis_for_processing(self):
        assert (
            _get_privacy_declaration_legal_basis_for_processing(
                data_use_legal_basis="Vital Interest",
                legitimate_interest_impact_assessment=None,
            )
            == "Vital interests"
        )

        assert (
            _get_privacy_declaration_legal_basis_for_processing(
                data_use_legal_basis="Vital Interest",
                legitimate_interest_impact_assessment="www.example.com/legitimate_interest_impact_assessments",
            )
            == "Legitimate interests"
        )

        assert (
            _get_privacy_declaration_legal_basis_for_processing(
                data_use_legal_basis=None,
                legitimate_interest_impact_assessment="www.example.com/legitimate_interest_impact_assessments",
            )
            == "Legitimate interests"
        )

        assert (
            _get_privacy_declaration_legal_basis_for_processing(
                data_use_legal_basis=None, legitimate_interest_impact_assessment=""
            )
            is None
        )

    def test_get_third_party_data(self):
        assert _get_third_party_data(recipients=None) == (False, None)

        assert _get_third_party_data(recipients="hello") == (False, None)

        assert _get_third_party_data(recipients=["advertisers"]) == (
            True,
            "advertisers",
        )

        assert _get_third_party_data(recipients=["advertisers", "marketing"]) == (
            True,
            "advertisers; marketing",
        )

        assert _get_third_party_data(
            recipients=["advertisers", "marketing", "BB&T bank"]
        ) == (True, "advertisers; marketing; BB&T bank")

    def test_get_retention_period(self):
        assert (
            _get_retention_period(retention_periods=None)
            == "No retention or erasure policy"
        )
        assert (
            _get_retention_period(retention_periods=[])
            == "No retention or erasure policy"
        )
        assert _get_retention_period(retention_periods=[None, "30 days"]) == "30 days"
        assert (
            _get_retention_period(retention_periods=["90 days", "3-7 years"])
            == "90 days"
        )
        assert (
            _get_retention_period(
                retention_periods=["No retention or erasure policy", "3-7 years"]
            )
            == "3-7 years"
        )
