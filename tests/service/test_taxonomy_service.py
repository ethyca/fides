import pytest
from sqlalchemy.exc import IntegrityError

from fides.api.common_exceptions import ValidationError
from fides.api.db.base_class import get_key_from_data
from fides.api.models.event_audit import EventAudit, EventAuditStatus, EventAuditType
from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    DataCategory,
    DataSubject,
    DataUse,
)
from fides.api.models.taxonomy import Taxonomy, TaxonomyUsage
from fides.api.service.deps import get_taxonomy_service
from fides.api.util.errors import ForbiddenIsDefaultTaxonomyError
from fides.service.event_audit_service import EventAuditService
from fides.service.taxonomy.handlers.legacy_handler import LegacyTaxonomyHandler
from fides.service.taxonomy.taxonomy_service import TaxonomyService
from fides.service.taxonomy.utils import generate_taxonomy_fides_key

LEGACY_TAXONOMY_TYPES = [
    "data_categories",
    "data_uses",
    "data_subjects",
]

HIERARCHICAL_TAXONOMY_TYPES = [
    "data_categories",
    "data_uses",
]


def _model_for_taxonomy(taxonomy_type: str):
    if taxonomy_type == "data_categories":
        return DataCategory
    if taxonomy_type == "data_uses":
        return DataUse
    if taxonomy_type == "data_subjects":
        return DataSubject
    raise ValueError("Unsupported taxonomy type for tests")


@pytest.fixture
def taxonomy_service(db):
    event_audit_service = EventAuditService(db)
    return TaxonomyService(db, event_audit_service)


class TestTaxonomyServiceGetters:

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_get_element_returns_element_when_exists(
        self, db, taxonomy_service, taxonomy_type
    ):
        element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "exists", "name": "Exists"}
        )
        db.flush()
        saved_element = taxonomy_service.get_element(taxonomy_type, "exists")
        assert (
            saved_element is not None and saved_element.fides_key == element.fides_key
        )

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_get_element_returns_none_when_missing(
        self, taxonomy_service, taxonomy_type
    ):
        assert taxonomy_service.get_element(taxonomy_type, "no_such_key") is None

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_get_elements_active_only_returns_only_active(
        self, db, taxonomy_service, taxonomy_type
    ):
        a_element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "a", "name": "A", "active": True}
        )
        b_element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "b", "name": "B", "active": False}
        )
        db.flush()
        elements = taxonomy_service.get_elements(taxonomy_type)
        assert all(e.active for e in elements)

        keys = {e.fides_key for e in elements}
        assert a_element.fides_key in keys and b_element.fides_key not in keys

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_get_elements_include_inactive_returns_all(
        self, db, taxonomy_service, taxonomy_type
    ):
        a_element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "a2", "name": "A2", "active": True}
        )
        b_element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "b2", "name": "B2", "active": False}
        )
        db.flush()
        elements = taxonomy_service.get_elements(taxonomy_type, active_only=False)
        keys = {e.fides_key for e in elements}
        assert {a_element.fides_key, b_element.fides_key}.issubset(keys)

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_get_elements_filtered_by_parent_key_active_only(
        self, db, taxonomy_service, taxonomy_type
    ):
        parent = taxonomy_service.create_element(
            taxonomy_type,
            {"fides_key": "pkey", "name": "P"},
        )
        active_child = taxonomy_service.create_element(
            taxonomy_type,
            {
                "fides_key": "pkey.child_active",
                "name": "CA",
                "parent_key": parent.fides_key,
            },
        )
        taxonomy_service.create_element(
            taxonomy_type,
            {
                "fides_key": "pkey.child_inactive",
                "name": "CI",
                "parent_key": parent.fides_key,
                "active": False,
            },
        )
        db.flush()

        results_active_only = taxonomy_service.get_elements(
            taxonomy_type, parent_key=parent.fides_key
        )
        assert all(element.active for element in results_active_only)
        assert {element.fides_key for element in results_active_only} == {
            active_child.fides_key
        }

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_get_elements_nonexistent_parent_returns_empty(
        self, taxonomy_service, taxonomy_type
    ):
        assert taxonomy_service.get_elements(taxonomy_type, parent_key="no.such") == []

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_get_elements_with_unsupported_taxonomy_raise_value_error(
        self, taxonomy_service, taxonomy_type
    ):
        with pytest.raises(ValueError):
            taxonomy_service.get_elements("not_supported")


class TestTaxonomyServiceCreate:
    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_create_element_with_explicit_key_succeeds(
        self, db, taxonomy_service, taxonomy_type
    ):
        element = taxonomy_service.create_element(
            taxonomy_type,
            {"fides_key": "custom_root", "name": "Custom Root"},
        )
        db.flush()
        saved_element = taxonomy_service.get_element(taxonomy_type, element.fides_key)
        assert saved_element is not None
        assert saved_element.fides_key == "custom_root"

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_create_element_generates_key_from_name(
        self, db, taxonomy_service, taxonomy_type
    ):
        name = "My Special Name"
        element = taxonomy_service.create_element(
            taxonomy_type,
            {"name": name},
        )
        db.flush()
        model_cls = _model_for_taxonomy(taxonomy_type)
        expected_key = get_key_from_data({"name": name}, model_cls.__name__)
        assert element.fides_key == expected_key

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_create_element_missing_name_and_key_fails(
        self, taxonomy_service, taxonomy_type
    ):
        with pytest.raises(Exception):
            taxonomy_service.create_element(taxonomy_type, {})

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_create_element_generates_hierarchical_key_with_parent(
        self, db, taxonomy_service, taxonomy_type
    ):
        parent = taxonomy_service.create_element(
            taxonomy_type,
            {"fides_key": "parent", "name": "Parent"},
        )
        db.flush()
        name = "Child One"
        child = taxonomy_service.create_element(
            taxonomy_type,
            {"name": name, "parent_key": parent.fides_key},
        )
        db.flush()
        model_cls = _model_for_taxonomy(taxonomy_type)
        expected_child_key = get_key_from_data({"name": name}, model_cls.__name__)
        assert child.fides_key == f"{parent.fides_key}.{expected_child_key}"

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_create_element_with_parent_in_wrong_taxonomy_raises_validation_error(
        self, db, taxonomy_service, taxonomy_type
    ):
        other_taxonomy = (
            "data_categories" if taxonomy_type == "data_uses" else "data_uses"
        )
        other_parent = taxonomy_service.create_element(
            other_taxonomy, {"fides_key": "other.parent", "name": "Other Parent"}
        )
        db.flush()
        with pytest.raises(ValidationError):
            taxonomy_service.create_element(
                taxonomy_type, {"name": "Child", "parent_key": other_parent.fides_key}
            )

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_create_element_with_nonexistent_parent_raises_validation_error(
        self, taxonomy_service, taxonomy_type
    ):
        with pytest.raises(ValidationError):
            taxonomy_service.create_element(
                taxonomy_type,
                {"name": "Child", "parent_key": "does.not.exist"},
            )

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_create_element_with_is_default_true_raises_forbidden_error(
        self, taxonomy_service, taxonomy_type
    ):
        with pytest.raises(ForbiddenIsDefaultTaxonomyError):
            taxonomy_service.create_element(
                taxonomy_type,
                {"name": "Default", "is_default": True},
            )

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_create_element_with_duplicate_key_raises_integrity_error(
        self, db, taxonomy_service, taxonomy_type
    ):
        taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "dupkey", "name": "DupKey"}
        )
        db.flush()
        with pytest.raises(IntegrityError):
            taxonomy_service.create_element(
                taxonomy_type, {"fides_key": "dupkey", "name": "DupKey Again"}
            )
            db.flush()
        db.rollback()


class TestTaxonomyServiceUpdate:
    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_update_nonexistent_element_returns_none(
        self, taxonomy_service, taxonomy_type
    ):
        assert (
            taxonomy_service.update_element(taxonomy_type, "nope", {"name": "X"})
            is None
        )

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_update_element_updates_basic_fields(
        self, db, taxonomy_service, taxonomy_type
    ):
        created = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "basic", "name": "Basic"}
        )
        db.flush()
        updated = taxonomy_service.update_element(
            taxonomy_type, created.fides_key, {"name": "Renamed"}
        )
        db.flush()
        assert updated.name == "Renamed"

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_update_element_set_active_false_deactivates_descendants_only(
        self, db, taxonomy_service, taxonomy_type
    ):
        root = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "r", "name": "R"}
        )
        child = taxonomy_service.create_element(
            taxonomy_type,
            {"fides_key": "r.c", "name": "C", "parent_key": root.fides_key},
        )
        grandchild = taxonomy_service.create_element(
            taxonomy_type,
            {"fides_key": "r.c.g", "name": "G", "parent_key": child.fides_key},
        )
        db.flush()

        updated = taxonomy_service.update_element(
            taxonomy_type, root.fides_key, {"active": False}
        )
        db.flush()
        assert updated.active is False
        assert (
            taxonomy_service.get_element(taxonomy_type, child.fides_key).active is False
        )
        assert (
            taxonomy_service.get_element(taxonomy_type, grandchild.fides_key).active
            is False
        )

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_update_element_set_active_true_activates_parents_only(
        self, db, taxonomy_service, taxonomy_type
    ):
        root = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "rr", "name": "RR", "active": False}
        )
        child = taxonomy_service.create_element(
            taxonomy_type,
            {
                "fides_key": "rr.cc",
                "name": "CC",
                "parent_key": root.fides_key,
                "active": False,
            },
        )
        grandchild = taxonomy_service.create_element(
            taxonomy_type,
            {
                "fides_key": "rr.cc.gg",
                "name": "GG",
                "parent_key": child.fides_key,
                "active": False,
            },
        )
        db.flush()

        updated_child = taxonomy_service.update_element(
            taxonomy_type, child.fides_key, {"active": True}
        )
        db.flush()
        assert updated_child.active is True
        assert (
            taxonomy_service.get_element(taxonomy_type, root.fides_key).active is True
        )
        assert (
            taxonomy_service.get_element(taxonomy_type, grandchild.fides_key).active
            is False
        )

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_update_element_active_true_idempotent(
        self, db, taxonomy_service, taxonomy_type
    ):
        node = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "idemp", "name": "I", "active": True}
        )
        db.flush()
        first = taxonomy_service.update_element(
            taxonomy_type, node.fides_key, {"active": True}
        )
        second = taxonomy_service.update_element(
            taxonomy_type, node.fides_key, {"active": True}
        )
        db.flush()
        assert first.active is True and second.active is True

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_update_element_active_false_idempotent(
        self, db, taxonomy_service, taxonomy_type
    ):
        node = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "idemp2", "name": "I2", "active": False}
        )
        db.flush()
        first = taxonomy_service.update_element(
            taxonomy_type, node.fides_key, {"active": False}
        )
        second = taxonomy_service.update_element(
            taxonomy_type, node.fides_key, {"active": False}
        )
        db.flush()
        assert first.active is False and second.active is False

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_update_element_change_parent_to_nonexistent_raises_validation_error(
        self, taxonomy_service, taxonomy_type
    ):
        created = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "moveme", "name": "Move Me"}
        )
        with pytest.raises(ValidationError):
            taxonomy_service.update_element(
                taxonomy_type, created.fides_key, {"parent_key": "nope.nope"}
            )

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_update_element_move_to_root_parent_none(
        self, db, taxonomy_service, taxonomy_type
    ):
        root = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "rootx", "name": "RootX"}
        )
        child = taxonomy_service.create_element(
            taxonomy_type,
            {
                "fides_key": "rootx.childx",
                "name": "ChildX",
                "parent_key": root.fides_key,
            },
        )
        db.flush()
        moved = taxonomy_service.update_element(
            taxonomy_type, child.fides_key, {"parent_key": None}
        )
        db.flush()
        assert moved.parent_key is None

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_update_element_change_parent_to_existing_parent(
        self, db, taxonomy_service, taxonomy_type
    ):
        p1 = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "p1", "name": "P1"}
        )
        p2 = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "p2", "name": "P2"}
        )
        child = taxonomy_service.create_element(
            taxonomy_type,
            {"fides_key": "p1.c", "name": "C", "parent_key": p1.fides_key},
        )
        db.flush()
        moved = taxonomy_service.update_element(
            taxonomy_type, child.fides_key, {"parent_key": p2.fides_key}
        )
        db.flush()
        assert moved.parent_key == p2.fides_key


class TestTaxonomyServiceDelete:
    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_delete_nonexistent_returns_false(self, taxonomy_service, taxonomy_type):
        taxonomy_service.delete_element(taxonomy_type, "missing")

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_delete_parent_with_children_raises_integrity_error_on_flush(
        self, db, taxonomy_service, taxonomy_type
    ):
        parent = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "dp", "name": "DP"}
        )
        taxonomy_service.create_element(
            taxonomy_type,
            {"fides_key": "dp.c1", "name": "C1", "parent_key": parent.fides_key},
        )

        with pytest.raises(IntegrityError):
            taxonomy_service.delete_element(taxonomy_type, parent.fides_key)

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_delete_children_then_parent_succeeds(
        self, db, taxonomy_service, taxonomy_type
    ):
        parent = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "pp", "name": "PP"}
        )
        child = taxonomy_service.create_element(
            taxonomy_type,
            {"fides_key": "pp.cc", "name": "CC", "parent_key": parent.fides_key},
        )
        taxonomy_service.delete_element(taxonomy_type, child.fides_key)
        taxonomy_service.delete_element(taxonomy_type, parent.fides_key)
        assert taxonomy_service.get_element(taxonomy_type, parent.fides_key) is None

    def test_delete_removes_taxonomy_usage_when_target_matches(
        self, db, taxonomy_service
    ):
        # Create a legacy element in data_categories
        taxonomy_type = "data_categories"
        element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "del_target", "name": "Del Target"}
        )

        # Create a custom taxonomy that applies to data_categories so we can insert a usage row
        Taxonomy.create(
            db,
            data={
                "fides_key": "custom_src",
                "name": "Custom Src",
                "applies_to": [taxonomy_type],
            },
        )

        # Insert a usage where the target matches the element to be deleted
        usage = TaxonomyUsage(
            source_element_key="custom_src.elem",
            target_element_key=element.fides_key,
            source_taxonomy="custom_src",
            target_taxonomy=taxonomy_type,
        )
        db.add(usage)
        db.flush()

        # Sanity check that usage exists
        assert (
            db.query(TaxonomyUsage)
            .filter(TaxonomyUsage.target_element_key == element.fides_key)
            .count()
            == 1
        )

        # Delete the element and ensure the usage row is removed
        taxonomy_service.delete_element(taxonomy_type, element.fides_key)
        assert (
            db.query(TaxonomyUsage)
            .filter(TaxonomyUsage.target_element_key == element.fides_key)
            .count()
            == 0
        )

    def test_delete_removes_taxonomy_usage_when_source_matches(
        self, db, taxonomy_service
    ):
        # Create a legacy element in data_uses
        taxonomy_type = "data_uses"
        element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "del_source", "name": "Del Source"}
        )

        # Create a custom taxonomy that applies to data_uses so we can insert a usage row
        Taxonomy.create(
            db,
            data={
                "fides_key": "custom_src2",
                "name": "Custom Src 2",
                "applies_to": [taxonomy_type],
            },
        )

        # Insert a usage where the source matches the element to be deleted
        usage = TaxonomyUsage(
            source_element_key=element.fides_key,
            target_element_key="some.target",
            source_taxonomy="custom_src2",
            target_taxonomy=taxonomy_type,
        )
        db.add(usage)
        db.flush()

        # Sanity check that usage exists
        assert (
            db.query(TaxonomyUsage)
            .filter(TaxonomyUsage.source_element_key == element.fides_key)
            .count()
            == 1
        )

        # Delete the element and ensure the usage row is removed
        taxonomy_service.delete_element(taxonomy_type, element.fides_key)
        assert (
            db.query(TaxonomyUsage)
            .filter(TaxonomyUsage.source_element_key == element.fides_key)
            .count()
            == 0
        )

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_delete_leaf_returns_true_and_removes_element(
        self, db, taxonomy_service, taxonomy_type
    ):
        leaf = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "leaf", "name": "Leaf"}
        )
        taxonomy_service.delete_element(taxonomy_type, leaf.fides_key)
        assert taxonomy_service.get_element(taxonomy_type, leaf.fides_key) is None


class TestTaxonomyServiceCreateOrUpdateReactivation:
    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_create_or_update_reactivates_inactive_element_by_name(
        self, db, taxonomy_service, taxonomy_type
    ):
        element = taxonomy_service.create_element(
            taxonomy_type, {"name": "Reactivate Me"}
        )
        db.flush()
        taxonomy_service.update_element(
            taxonomy_type, element.fides_key, {"active": False}
        )
        db.flush()

        reactivated = taxonomy_service.create_or_update_element(
            taxonomy_type, {"name": "Reactivate Me"}
        )
        db.flush()
        assert reactivated.active is True

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_create_or_update_reactivation_activates_parents(
        self, db, taxonomy_service, taxonomy_type
    ):
        parent = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "rxp", "name": "RXP", "active": False}
        )
        taxonomy_service.create_element(
            taxonomy_type,
            {
                "fides_key": "rxp.child",
                "name": "RChild",
                "parent_key": parent.fides_key,
                "active": False,
            },
        )
        db.flush()
        reactivated = taxonomy_service.create_or_update_element(
            taxonomy_type, {"name": "RChild"}
        )
        db.flush()
        assert reactivated.active is True
        assert (
            taxonomy_service.get_element(taxonomy_type, parent.fides_key).active is True
        )

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_create_or_update_with_fides_key_does_not_reactivate_attempts_create(
        self, db, taxonomy_service, taxonomy_type
    ):
        element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "dupe", "name": "Dupe"}
        )
        db.flush()
        taxonomy_service.update_element(
            taxonomy_type, element.fides_key, {"active": False}
        )
        db.flush()
        with pytest.raises(IntegrityError):
            taxonomy_service.create_or_update_element(
                taxonomy_type, {"fides_key": "dupe", "name": "Other"}
            )
            db.flush()
        db.rollback()

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_create_or_update_name_mismatch_does_not_reactivate_creates_new(
        self, db, taxonomy_service, taxonomy_type
    ):
        element = taxonomy_service.create_element(
            taxonomy_type, {"name": "Stay Inactive"}
        )
        db.flush()
        taxonomy_service.update_element(
            taxonomy_type, element.fides_key, {"active": False}
        )
        db.flush()
        new_elem = taxonomy_service.create_or_update_element(
            taxonomy_type, {"name": "Different"}
        )
        db.flush()
        assert new_elem.fides_key != element.fides_key
        assert (
            taxonomy_service.get_element(taxonomy_type, element.fides_key).active
            is False
        )

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_create_or_update_reactivation_updates_additional_fields(
        self, db, taxonomy_service, taxonomy_type
    ):
        element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "rad", "name": "RAD", "active": True}
        )
        db.flush()
        taxonomy_service.update_element(
            taxonomy_type, element.fides_key, {"active": False}
        )
        db.flush()
        updated = taxonomy_service.create_or_update_element(
            taxonomy_type, {"name": "RAD", "description": "newdesc"}
        )
        db.flush()
        assert updated.active is True
        if hasattr(updated, "description"):
            assert updated.description == "newdesc"

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_create_or_update_without_name_and_key_fails(
        self, taxonomy_service, taxonomy_type
    ):
        with pytest.raises(Exception):
            taxonomy_service.create_or_update_element(taxonomy_type, {})

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_create_or_update_reactivation_with_is_default_in_payload_sets_flag(
        self, db, taxonomy_service, taxonomy_type
    ):
        element = taxonomy_service.create_element(
            taxonomy_type, {"name": "Default Toggle"}
        )
        db.flush()
        taxonomy_service.update_element(
            taxonomy_type, element.fides_key, {"active": False}
        )
        db.flush()

        updated = taxonomy_service.create_or_update_element(
            taxonomy_type, {"name": "Default Toggle", "is_default": True}
        )
        db.flush()
        assert updated.active is True
        if hasattr(updated, "is_default"):
            assert updated.is_default is True

    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_create_or_update_reactivation_with_parent_key_sets_generated_key(
        self, db, taxonomy_service, taxonomy_type
    ):
        base_name = "Reparent Me"
        element = taxonomy_service.create_element(taxonomy_type, {"name": base_name})
        db.flush()
        taxonomy_service.update_element(
            taxonomy_type, element.fides_key, {"active": False}
        )
        db.flush()

        parent = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "newparent", "name": "New Parent"}
        )
        db.flush()

        reactivated = taxonomy_service.create_or_update_element(
            taxonomy_type, {"name": base_name, "parent_key": parent.fides_key}
        )
        db.flush()

        model_cls = _model_for_taxonomy(taxonomy_type)
        expected_child = get_key_from_data({"name": base_name}, model_cls.__name__)
        assert reactivated.fides_key == f"{parent.fides_key}.{expected_child}"


class TestTaxonomyServiceAuditEvents:
    """Tests that TaxonomyService creates appropriate audit events."""

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_create_element_creates_audit_event(self, db, taxonomy_service, taxonomy_type):
        """Test that creating taxonomy elements creates audit events."""
        # Count audit events before operation
        initial_count = db.query(EventAudit).count()

        element_data = {"fides_key": "audit_test", "name": "Audit Test"}
        element = taxonomy_service.create_element(taxonomy_type, element_data)
        db.flush()

        # Verify audit event was created
        audit_events = db.query(EventAudit).filter(
            EventAudit.event_type == EventAuditType.taxonomy_element_created.value
        ).all()
        assert len(audit_events) == initial_count + 1

        # Verify audit event details
        audit_event = audit_events[-1]  # Get the most recent one
        assert audit_event.resource_type == "taxonomy_element"
        assert audit_event.resource_identifier == element.fides_key
        assert audit_event.status == EventAuditStatus.succeeded
        assert f"Created {taxonomy_type} element: {element.fides_key}" in audit_event.description
        assert audit_event.event_details["taxonomy_type"] == taxonomy_type
        assert audit_event.event_details["fides_key"] == element.fides_key
        assert audit_event.event_details["name"] == element_data["name"]

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_update_element_creates_audit_event(self, db, taxonomy_service, taxonomy_type):
        """Test that updating taxonomy elements creates audit events."""
        # Create element first
        element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "update_test", "name": "Update Test"}
        )
        db.flush()

        # Count audit events before update
        initial_count = db.query(EventAudit).filter(
            EventAudit.event_type == EventAuditType.taxonomy_element_updated.value
        ).count()

        # Update the element
        update_data = {"name": "Updated Test Name", "description": "Updated description"}
        updated_element = taxonomy_service.update_element(
            taxonomy_type, element.fides_key, update_data
        )
        db.flush()

        # Verify audit event was created
        audit_events = db.query(EventAudit).filter(
            EventAudit.event_type == EventAuditType.taxonomy_element_updated.value
        ).all()
        assert len(audit_events) == initial_count + 1

        # Verify audit event details
        audit_event = audit_events[-1]  # Get the most recent one
        assert audit_event.resource_type == "taxonomy_element"
        assert audit_event.resource_identifier == element.fides_key
        assert audit_event.status == EventAuditStatus.succeeded
        assert f"Updated {taxonomy_type} element: {element.fides_key}" in audit_event.description
        assert audit_event.event_details["taxonomy_type"] == taxonomy_type
        assert audit_event.event_details["name"] == update_data["name"]
        assert audit_event.event_details["description"] == update_data["description"]

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_delete_element_creates_audit_event(self, db, taxonomy_service, taxonomy_type):
        """Test that deleting taxonomy elements creates audit events."""
        # Create element first
        element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "delete_test", "name": "Delete Test"}
        )
        db.flush()

        # Count audit events before delete
        initial_count = db.query(EventAudit).filter(
            EventAudit.event_type == EventAuditType.taxonomy_element_deleted.value
        ).count()

        # Delete the element
        taxonomy_service.delete_element(taxonomy_type, element.fides_key)

        # Verify audit event was created
        audit_events = db.query(EventAudit).filter(
            EventAuditType.taxonomy_element_deleted.value
        ).all()
        assert len(audit_events) == initial_count + 1

        # Verify audit event details
        audit_event = audit_events[-1]  # Get the most recent one
        assert audit_event.resource_type == "taxonomy_element"
        assert audit_event.resource_identifier == element.fides_key
        assert audit_event.status == EventAuditStatus.succeeded
        assert f"Deleted {taxonomy_type} element: {element.fides_key}" in audit_event.description
        assert audit_event.event_details["taxonomy_type"] == taxonomy_type

    def test_multiple_operations_create_multiple_audit_events(self, db, taxonomy_service):
        """Test that multiple operations create separate audit events."""
        taxonomy_type = "data_categories"

        # Track initial audit event count
        initial_count = db.query(EventAudit).count()

        # Create element
        element = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "multi_test", "name": "Multi Test"}
        )
        db.flush()

        # Update element
        taxonomy_service.update_element(
            taxonomy_type, element.fides_key, {"name": "Multi Test Updated"}
        )
        db.flush()

        # Delete element
        taxonomy_service.delete_element(taxonomy_type, element.fides_key)

        # Verify we have 3 new audit events
        final_count = db.query(EventAudit).count()
        assert final_count == initial_count + 3

        # Verify we have one of each type of event
        created_events = db.query(EventAudit).filter(
            EventAudit.event_type == EventAuditType.taxonomy_element_created.value,
            EventAudit.resource_identifier == element.fides_key
        ).count()
        updated_events = db.query(EventAudit).filter(
            EventAudit.event_type == EventAuditType.taxonomy_element_updated.value,
            EventAudit.resource_identifier == element.fides_key
        ).count()
        deleted_events = db.query(EventAudit).filter(
            EventAudit.event_type == EventAuditType.taxonomy_element_deleted.value,
            EventAudit.resource_identifier == element.fides_key
        ).count()

        assert created_events == 1
        assert updated_events == 1
        assert deleted_events == 1


class TestTaxonomyServiceCascadesAndHierarchy:
    @pytest.mark.parametrize("taxonomy_type", HIERARCHICAL_TAXONOMY_TYPES)
    def test_get_elements_after_cascades_respects_active_only_flag(
        self, db, taxonomy_service, taxonomy_type
    ):
        root = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "croot", "name": "CRoot"}
        )
        child = taxonomy_service.create_element(
            taxonomy_type,
            {
                "fides_key": "croot.child",
                "name": "CChild",
                "parent_key": root.fides_key,
            },
        )
        taxonomy_service.create_element(
            taxonomy_type,
            {
                "fides_key": "croot.child.grand",
                "name": "CGrand",
                "parent_key": child.fides_key,
            },
        )
        db.flush()

        taxonomy_service.update_element(
            taxonomy_type, child.fides_key, {"active": False}
        )
        db.flush()

        active_only = taxonomy_service.get_elements(
            taxonomy_type, parent_key=root.fides_key, active_only=True
        )
        include_inactive = taxonomy_service.get_elements(
            taxonomy_type, parent_key=root.fides_key, active_only=False
        )

        assert {e.fides_key for e in active_only} == set()
        assert {e.fides_key for e in include_inactive} == {child.fides_key}


class TestTaxonomyServiceRoundTrip:
    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_round_trip_create_get_update_delete(
        self, db, taxonomy_service, taxonomy_type
    ):
        created = taxonomy_service.create_element(
            taxonomy_type, {"fides_key": "rt", "name": "RoundTrip"}
        )
        db.flush()
        got = taxonomy_service.get_element(taxonomy_type, created.fides_key)
        assert got is not None
        updated = taxonomy_service.update_element(
            taxonomy_type, created.fides_key, {"name": "Updated"}
        )
        db.flush()
        assert updated.name == "Updated"

        taxonomy_service.delete_element(taxonomy_type, created.fides_key)
        db.flush()
        assert taxonomy_service.get_element(taxonomy_type, created.fides_key) is None


class TestTaxonomyServiceDI:
    def test_dependency_factory_returns_service_instance(self, db):
        taxonomy_service = get_taxonomy_service(db)
        assert isinstance(taxonomy_service, TaxonomyService)


class TestTaxonomyServiceKeyGeneration:
    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_generate_key_from_name_slugifies_and_lowercases(self, db, taxonomy_type):
        handler = LegacyTaxonomyHandler(db, taxonomy_type)
        name = "My Special Name"
        generated_key = generate_taxonomy_fides_key(
            taxonomy_type, name, handler=handler
        )
        model_cls = _model_for_taxonomy(taxonomy_type)
        expected = get_key_from_data({"name": name}, model_cls.__name__)
        assert generated_key == expected

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_generate_key_with_parent_prefixes_parent_key(self, db, taxonomy_type):
        handler = LegacyTaxonomyHandler(db, taxonomy_type)
        name = "Child"
        parent_key = "parent"
        generated_key = generate_taxonomy_fides_key(
            taxonomy_type, name, parent_key=parent_key, handler=handler
        )
        model_cls = _model_for_taxonomy(taxonomy_type)
        expected_child = get_key_from_data({"name": name}, model_cls.__name__)
        assert generated_key == f"{parent_key}.{expected_child}"

    @pytest.mark.parametrize("taxonomy_type", LEGACY_TAXONOMY_TYPES)
    def test_generate_key_is_stable_for_same_inputs(self, db, taxonomy_type):
        handler = LegacyTaxonomyHandler(db, taxonomy_type)
        name = "Stability Check"
        first_key = generate_taxonomy_fides_key(taxonomy_type, name, handler=handler)
        second_key = generate_taxonomy_fides_key(taxonomy_type, name, handler=handler)
        assert first_key == second_key
