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
                            "fides_meta": {
                                "data_categories": ["user.contact.email.existing"]
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
                            "fides_meta": {
                                "data_categories": ["user.contact.email.template"]
                            },
                            "data_type": "string",
                        }
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        field = result["collections"][0]["fields"][0]
        # Should preserve existing fides_meta data_categories
        assert field["fides_meta"]["data_categories"] == ["user.contact.email.existing"]
        # Should adopt new template properties
        assert field["data_type"] == "string"

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
                            "fides_meta": {
                                "data_categories": ["user.contact.email.existing"]
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
                            "fides_meta": {
                                "data_categories": ["user.contact.email.template"]
                            },
                        },
                        {
                            "name": "username",
                            "fides_meta": {"data_categories": ["user.name"]},
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
        assert email_field["fides_meta"]["data_categories"] == [
            "user.contact.email.existing"
        ]

        # New field should get template data_categories
        username_field = next(f for f in fields if f["name"] == "username")
        assert username_field["fides_meta"]["data_categories"] == ["user.name"]

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
                                    "fides_meta": {
                                        "data_categories": [
                                            "user.contact.address.street.existing"
                                        ]
                                    },
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
                                    "fides_meta": {
                                        "data_categories": [
                                            "user.contact.address.street.template"
                                        ]
                                    },
                                    "data_type": "string",
                                },
                                {
                                    "name": "city",
                                    "fides_meta": {
                                        "data_categories": ["user.contact.address.city"]
                                    },
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
        assert street_field["fides_meta"]["data_categories"] == [
            "user.contact.address.street.existing"
        ]
        assert street_field["data_type"] == "string"  # Should adopt new properties

        # New nested field should get template data_categories
        city_field = next(f for f in nested_fields if f["name"] == "city")
        assert city_field["fides_meta"]["data_categories"] == [
            "user.contact.address.city"
        ]

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
                            # No fides_meta or data_categories
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
                            "fides_meta": {
                                "data_categories": ["user.contact.email.template"]
                            },
                        }
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        field = result["collections"][0]["fields"][0]
        # Should get template data_categories since existing had none
        assert field["fides_meta"]["data_categories"] == ["user.contact.email.template"]

    def test_merge_handles_null_fides_meta(self):
        """Test that null fides_meta is handled gracefully"""
        existing_dataset = {
            "fides_key": "test_dataset",
            "collections": [
                {"name": "users", "fields": [{"name": "email", "fides_meta": None}]}
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
                            "fides_meta": {
                                "data_categories": ["user.contact.email.template"]
                            },
                        }
                    ],
                }
            ],
        }

        result = merge_dataset_dicts(existing_dataset, template_dataset)

        field = result["collections"][0]["fields"][0]
        # Should get template data_categories since existing fides_meta was null
        assert field["fides_meta"]["data_categories"] == ["user.contact.email.template"]

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
                            "fides_meta": {
                                "data_categories": ["user.financial.account_balance"]
                            },
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
        assert orders_collection["fields"][0]["fides_meta"]["data_categories"] == [
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
                            "fides_meta": {
                                "data_categories": ["user.contact.email.existing"]
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
                    "data_categories": ["user.template.collection"],
                    "fields": [
                        {
                            "name": "email",
                            "fides_meta": {
                                "data_categories": ["user.contact.email.template"]
                            },
                            "data_type": "string",
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
        assert field["fides_meta"]["data_categories"] == ["user.contact.email.existing"]
        # But should adopt other template properties
        assert field["data_type"] == "string"
