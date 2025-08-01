"""Tests for the merge_dataset_dicts function in connector_registry_service.py"""

from fides.api.service.connectors.saas.connector_registry_service import (
    merge_dataset_dicts,
)


class TestMergeDatasetDicts:
    """Test the merge_dataset_dicts function behavior"""

    def test_merge_preserves_collection_data_categories(self):
        """Test that collection-level data_categories are preserved from existing dataset"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "data_categories": ["user.existing.category"],
                    "fields": [],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "data_categories": ["user.template.category"],
                    "fields": [
                        {"name": "id", "data_categories": ["system.operations"]}
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        # Should preserve existing collection data_categories
        assert result["collections"][0]["data_categories"] == ["user.existing.category"]
        # Should adopt new template structure (new fields)
        assert len(result["collections"][0]["fields"]) == 1
        assert result["collections"][0]["fields"][0]["name"] == "id"

    def test_merge_preserves_field_data_categories(self):
        """Test that field-level data_categories are preserved from existing dataset"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.existing"],
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.template"],
                            "fides_meta": {
                                "data_type": "string",
                            },
                        }
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        field = result["collections"][0]["fields"][0]
        # Should preserve existing data_categories
        assert field["data_categories"] == ["user.contact.email.existing"]
        # Should adopt new template properties
        assert field["fides_meta"]["data_type"] == "string"

    def test_merge_handles_new_fields_in_template(self):
        """Test that new fields from template are added with their data_categories"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.existing"],
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.template"],
                        },
                        {
                            "name": "username",
                            "data_categories": ["user.name"],
                        },
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        fields = result["collections"][0]["fields"]
        assert len(fields) == 2

        # Existing field should preserve its data_categories
        email_field = next(f for f in fields if f["name"] == "email")
        assert email_field["data_categories"] == ["user.contact.email.existing"]

        # New field should get template data_categories
        username_field = next(f for f in fields if f["name"] == "username")
        assert username_field["data_categories"] == ["user.name"]

    def test_merge_handles_nested_fields(self):
        """Test that nested fields preserve data_categories correctly"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "address",
                            "fields": [
                                {
                                    "name": "street",
                                    "data_categories": [
                                        "user.contact.address.street.existing"
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "address",
                            "fields": [
                                {
                                    "name": "street",
                                    "data_categories": [
                                        "user.contact.address.street.template"
                                    ],
                                    "fides_meta": {
                                        "data_type": "string",
                                    },
                                },
                                {
                                    "name": "city",
                                    "data_categories": ["user.contact.address.city"],
                                },
                            ],
                        }
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        address_field = result["collections"][0]["fields"][0]
        nested_fields = address_field["fields"]

        # Existing nested field should preserve data_categories
        street_field = next(f for f in nested_fields if f["name"] == "street")
        assert street_field["data_categories"] == [
            "user.contact.address.street.existing"
        ]
        assert (
            street_field["fides_meta"]["data_type"] == "string"
        )  # Should adopt new properties

        # New nested field should get template data_categories
        city_field = next(f for f in nested_fields if f["name"] == "city")
        assert city_field["data_categories"] == ["user.contact.address.city"]

    def test_merge_handles_missing_existing_data_categories(self):
        """Test that fields without existing data_categories get template ones"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email"
                            # No data_categories
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.template"],
                        }
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        field = result["collections"][0]["fields"][0]
        # Should get template data_categories since existing had none
        assert field["data_categories"] == ["user.contact.email.template"]

    def test_merge_preserves_fides_meta_structure(self):
        """Test that fides_meta is preserved correctly while data_categories are handled separately"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.existing"],
                            "fides_meta": {
                                "primary_key": True,
                                "read_only": True,
                            },
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.template"],
                            "fides_meta": {
                                "data_type": "string",
                            },
                        }
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        field = result["collections"][0]["fields"][0]
        # Should preserve existing data_categories
        assert field["data_categories"] == ["user.contact.email.existing"]
        # Should adopt template fides_meta
        assert field["fides_meta"]["data_type"] == "string"
        # Should NOT preserve existing fides_meta since it's not in preserved_properties
        assert "primary_key" not in field["fides_meta"]
        assert "read_only" not in field["fides_meta"]

    def test_merge_handles_new_collections(self):
        """Test that new collections from template are added completely"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {"name": "users", "data_categories": ["user.existing"], "fields": []}
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {"name": "users", "data_categories": ["user.template"], "fields": []},
                {
                    "name": "orders",
                    "data_categories": ["user.financial"],
                    "fields": [
                        {
                            "name": "total",
                            "data_categories": ["user.financial.account_balance"],
                        }
                    ],
                },
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        assert len(result["collections"]) == 2

        # Existing collection should preserve its data_categories
        users_collection = next(
            c for c in result["collections"] if c["name"] == "users"
        )
        assert users_collection["data_categories"] == ["user.existing"]

        # New collection should get template data_categories
        orders_collection = next(
            c for c in result["collections"] if c["name"] == "orders"
        )
        assert orders_collection["data_categories"] == ["user.financial"]
        assert orders_collection["fields"][0]["data_categories"] == [
            "user.financial.account_balance"
        ]

    def test_merge_preserves_both_collection_and_field_data_categories(self):
        """Test that both collection-level and field-level data_categories are preserved"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "data_categories": ["user.existing.collection"],
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.existing"],
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "data_categories": ["user.template.collection"],
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.template"],
                            "fides_meta": {
                                "data_type": "string",
                            },
                        }
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        collection = result["collections"][0]
        # Collection level should preserve existing
        assert collection["data_categories"] == ["user.existing.collection"]

        field = collection["fields"][0]
        # Field level should preserve existing
        assert field["data_categories"] == ["user.contact.email.existing"]
        # But should adopt other template properties
        assert field["fides_meta"]["data_type"] == "string"

    def test_preserved_properties_parameter_works(self):
        """Test that the preserved_properties parameter works for additional properties"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "description": "Existing users description",
                    "data_categories": ["user.existing.category"],
                    "fields": [
                        {
                            "name": "email",
                            "description": "Existing email description",
                            "data_categories": ["user.contact.email.existing"],
                            "fides_meta": {
                                "data_type": "string",
                                "primary_key": True,
                                "read_only": True,
                            },
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "description": "Template users description",
                    "data_categories": ["user.template.category"],
                    "fields": [
                        {
                            "name": "email",
                            "description": "Template email description",
                            "data_categories": ["user.contact.email.template"],
                            "fides_meta": {
                                "data_type": "text",
                                "primary_key": False,
                                "length": 255,
                            },
                        }
                    ],
                }
            ],
        }

        # Test with additional preserved properties
        result = merge_dataset_dicts(
            existing_dataset,
            template_dataset,
            preserved_properties=["data_categories", "description"],
        )

        collection = result["collections"][0]
        # Should preserve existing data_categories and description
        assert collection["data_categories"] == ["user.existing.category"]
        assert collection["description"] == "Existing users description"

        field = collection["fields"][0]
        # Should preserve existing data_categories and description
        assert field["data_categories"] == ["user.contact.email.existing"]
        assert field["description"] == "Existing email description"
        # fides_meta should come from template since it's not preserved
        assert field["fides_meta"]["data_type"] == "text"
        assert field["fides_meta"]["primary_key"] == False
        assert field["fides_meta"]["length"] == 255
        assert "read_only" not in field["fides_meta"]

    def test_preserved_properties_for_nested_metadata(self):
        """Test preserving specific nested metadata properties using dot notation"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.existing"],
                            "fides_meta": {
                                "data_type": "varchar",
                                "primary_key": True,
                                "read_only": True,
                            },
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email.template"],
                            "fides_meta": {
                                "data_type": "text",
                                "primary_key": False,
                                "length": 255,
                            },
                        }
                    ],
                }
            ],
        }

        # Test 1: Preserve specific nested property with dot notation
        result1 = merge_dataset_dicts(
            existing_dataset,
            template_dataset,
            preserved_properties=["data_categories", "fides_meta.data_type"],
        )

        field1 = result1["collections"][0]["fields"][0]
        # Should preserve data_categories
        assert field1["data_categories"] == ["user.contact.email.existing"]

        # Should preserve only the specific nested property
        assert (
            field1["fides_meta"]["data_type"] == "varchar"
        )  # From existing (preserved)
        assert (
            field1["fides_meta"]["primary_key"] == False
        )  # From template (not preserved)
        assert field1["fides_meta"]["length"] == 255  # From template (new property)
        assert "read_only" not in field1["fides_meta"]  # Not in template

        # Test 2: Preserve multiple nested properties with dot notation
        result2 = merge_dataset_dicts(
            existing_dataset,
            template_dataset,
            preserved_properties=[
                "data_categories",
                "fides_meta.data_type",
                "fides_meta.primary_key",
            ],
        )

        field2 = result2["collections"][0]["fields"][0]
        # Should preserve data_categories
        assert field2["data_categories"] == ["user.contact.email.existing"]

        # Should preserve specific nested properties
        assert (
            field2["fides_meta"]["data_type"] == "varchar"
        )  # From existing (preserved)
        assert field2["fides_meta"]["primary_key"] == True  # From existing (preserved)
        assert field2["fides_meta"]["length"] == 255  # From template (not preserved)
        assert "read_only" not in field2["fides_meta"]  # Not in template

        # Test 3: Preserve entire fides_meta object (old behavior still works)
        result3 = merge_dataset_dicts(
            existing_dataset,
            template_dataset,
            preserved_properties=["data_categories", "fides_meta"],
        )

        field3 = result3["collections"][0]["fields"][0]
        # Should preserve data_categories
        assert field3["data_categories"] == ["user.contact.email.existing"]

        # Should preserve entire fides_meta from existing
        assert field3["fides_meta"]["data_type"] == "varchar"  # From existing
        assert field3["fides_meta"]["primary_key"] == True  # From existing
        assert field3["fides_meta"]["read_only"] == True  # From existing
        assert "length" not in field3["fides_meta"]  # Not in existing

    def test_dot_notation_nested_deeper(self):
        """Test dot notation with deeper nesting levels"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "profile",
                            "data_categories": ["user.existing"],
                            "nested_config": {
                                "database": {
                                    "connection": {
                                        "type": "existing_postgres",
                                        "timeout": 30,
                                    }
                                },
                                "validation": {"required": True},
                            },
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "profile",
                            "data_categories": ["user.template"],
                            "nested_config": {
                                "database": {
                                    "connection": {
                                        "type": "template_mysql",
                                        "host": "localhost",
                                    }
                                },
                                "validation": {"required": False, "format": "email"},
                            },
                        }
                    ],
                }
            ],
        }

        # Test preserving deeply nested properties
        result = merge_dataset_dicts(
            existing_dataset,
            template_dataset,
            preserved_properties=[
                "data_categories",
                "nested_config.database.connection.type",
                "nested_config.validation.required",
            ],
        )

        field = result["collections"][0]["fields"][0]

        # Should preserve data_categories
        assert field["data_categories"] == ["user.existing"]

        # Should preserve specific deeply nested properties
        assert (
            field["nested_config"]["database"]["connection"]["type"]
            == "existing_postgres"
        )  # Preserved
        assert (
            field["nested_config"]["database"]["connection"]["host"] == "localhost"
        )  # From template
        assert field["nested_config"]["validation"]["required"] == True  # Preserved
        assert (
            field["nested_config"]["validation"]["format"] == "email"
        )  # From template

        # Should not preserve non-specified nested properties
        assert (
            "timeout" not in field["nested_config"]["database"]["connection"]
        )  # Not preserved

    def test_dot_notation_missing_paths(self):
        """Test dot notation behavior when paths don't exist in existing data"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.existing"],
                            # No fides_meta at all
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.template"],
                            "fides_meta": {
                                "data_type": "text",
                                "length": 255,
                            },
                        }
                    ],
                }
            ],
        }

        # Test with dot notation for non-existent path
        result = merge_dataset_dicts(
            existing_dataset,
            template_dataset,
            preserved_properties=["data_categories", "fides_meta.data_type"],
        )

        field = result["collections"][0]["fields"][0]

        # Should preserve existing data_categories
        assert field["data_categories"] == ["user.existing"]

        # Should use template values when existing path doesn't exist
        assert (
            field["fides_meta"]["data_type"] == "text"
        )  # From template (nothing to preserve)
        assert field["fides_meta"]["length"] == 255  # From template

    def test_preserved_properties_comprehensive_capabilities(self):
        """Demonstrate all capabilities of the preserved_properties parameter"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "dataset_description": "Existing dataset description",
            "collections": [
                {
                    "name": "users",
                    "description": "Existing collection description",
                    "data_categories": ["user.existing"],
                    "custom_property": "existing_value",
                    "fields": [
                        {
                            "name": "email",
                            "description": "Existing field description",
                            "data_categories": ["user.contact.email.existing"],
                            "custom_field_prop": "existing_field_value",
                            "fides_meta": {
                                "data_type": "varchar",
                                "primary_key": True,
                                "indexed": True,
                            },
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "dataset_description": "Template dataset description",
            "collections": [
                {
                    "name": "users",
                    "description": "Template collection description",
                    "data_categories": ["user.template"],
                    "custom_property": "template_value",
                    "new_property": "template_new",
                    "fields": [
                        {
                            "name": "email",
                            "description": "Template field description",
                            "data_categories": ["user.contact.email.template"],
                            "custom_field_prop": "template_field_value",
                            "new_field_prop": "template_new_field",
                            "fides_meta": {
                                "data_type": "text",
                                "length": 255,
                                "nullable": False,
                            },
                        }
                    ],
                }
            ],
        }

        # Test comprehensive preservation with mix of simple and dot notation properties
        result = merge_dataset_dicts(
            existing_dataset,
            template_dataset,
            preserved_properties=[
                "data_categories",  # Simple property (default)
                "description",  # Simple property at all levels
                "custom_property",  # Simple custom property at collection level
                "custom_field_prop",  # Simple custom property at field level
                "fides_meta.data_type",  # Nested property with dot notation
                "fides_meta.primary_key",  # Another nested property
                "dataset_description",  # Dataset-level property
            ],
        )

        # Dataset level properties
        assert (
            result["dataset_description"] == "Existing dataset description"
        )  # Preserved

        collection = result["collections"][0]
        # Collection properties
        assert collection["data_categories"] == ["user.existing"]  # Preserved
        assert (
            collection["description"] == "Existing collection description"
        )  # Preserved
        assert collection["custom_property"] == "existing_value"  # Preserved
        assert (
            collection["new_property"] == "template_new"
        )  # From template (not preserved)

        field = collection["fields"][0]
        # Field properties
        assert field["data_categories"] == ["user.contact.email.existing"]  # Preserved
        assert field["description"] == "Existing field description"  # Preserved
        assert field["custom_field_prop"] == "existing_field_value"  # Preserved
        assert (
            field["new_field_prop"] == "template_new_field"
        )  # From template (not preserved)

        # Nested properties with dot notation - granular preservation
        assert (
            field["fides_meta"]["data_type"] == "varchar"
        )  # From existing (preserved)
        assert field["fides_meta"]["primary_key"] == True  # From existing (preserved)
        assert field["fides_meta"]["length"] == 255  # From template (not preserved)
        assert field["fides_meta"]["nullable"] == False  # From template (not preserved)
        assert "indexed" not in field["fides_meta"]  # Not in template

    def test_merge_preserves_specific_child_fields_when_template_has_generic_object(
        self,
    ):
        """Test that specific child fields are preserved when template only has generic object field"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "address",
                            "data_categories": ["user.contact.address.custom"],
                            "fields": [
                                {
                                    "name": "street",
                                    "data_categories": ["user.contact.address.street"],
                                },
                                {
                                    "name": "city",
                                    "data_categories": ["user.contact.address.city"],
                                },
                                {
                                    "name": "zipcode",
                                    "data_categories": [
                                        "user.contact.address.postal_code"
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "address",
                            "data_categories": ["user.contact.address.template"],
                            "fides_meta": {
                                "data_type": "object",
                                "description": "User address information",
                            },
                        }
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        address_field = result["collections"][0]["fields"][0]

        # Should preserve existing data_categories
        assert address_field["data_categories"] == ["user.contact.address.custom"]

        # Should adopt template metadata
        assert address_field["fides_meta"]["data_type"] == "object"
        assert address_field["fides_meta"]["description"] == "User address information"

        # Should preserve the specific child fields from existing dataset
        assert "fields" in address_field, "Should preserve existing nested fields"
        assert len(address_field["fields"]) == 3

        # Verify all child fields are preserved
        field_names = [f["name"] for f in address_field["fields"]]
        assert "street" in field_names
        assert "city" in field_names
        assert "zipcode" in field_names

        # Verify child field data categories are preserved
        street_field = next(f for f in address_field["fields"] if f["name"] == "street")
        assert street_field["data_categories"] == ["user.contact.address.street"]

        city_field = next(f for f in address_field["fields"] if f["name"] == "city")
        assert city_field["data_categories"] == ["user.contact.address.city"]

        zipcode_field = next(
            f for f in address_field["fields"] if f["name"] == "zipcode"
        )
        assert zipcode_field["data_categories"] == ["user.contact.address.postal_code"]
