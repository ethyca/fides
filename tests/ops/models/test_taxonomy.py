import pytest
from sqlalchemy.exc import IntegrityError
from fides.api.common_exceptions import ValidationError
from sqlalchemy.orm import Session

from fides.api.models.taxonomy import (
    Taxonomy,
    TaxonomyElement,
    TaxonomyUsage,
)


@pytest.mark.usefixtures("default_taxonomy")
class TestTaxonomyModels:

    def test_cannot_create_legacy_taxonomy(self, db: Session):
        """Legacy taxonomy keys are system-managed and cannot be created via the new model."""
        with pytest.raises(ValidationError):
            Taxonomy.create(
                db=db,
                data={
                    "fides_key": "data_categories",
                    "name": "Data Categories",
                },
            )

    def test_can_create_custom_taxonomy(self, db: Session):
        """Custom taxonomies can be created."""
        Taxonomy.create(
            db=db,
            data={
                "fides_key": "sensitivity",
                "name": "Sensitivity",
                "applies_to": ["data_categories"],
            },
        )

    def test_can_update_applies_to_with_legacy_taxonomy(self, db: Session):
        """Taxonomy applies_to can be updated."""
        taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )
        updated_taxonomy = taxonomy.update(
            db=db, data={"applies_to": ["data_categories"]}
        )
        db.flush()
        assert updated_taxonomy.applies_to == ["data_categories"]

    def test_can_update_applies_to_with_custom_taxonomy(self, db: Session):
        """Taxonomy applies_to can be updated."""
        sensitivity_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )
        severity_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "severity", "name": "Severity"},
        )

        updated_taxonomy = sensitivity_taxonomy.update(
            db=db, data={"applies_to": [severity_taxonomy.fides_key]}
        )
        db.flush()
        assert updated_taxonomy.applies_to == ["severity"]

    def test_applies_to_is_idempotent(self, db: Session):
        """Setting the same target taxonomy twice should not create duplicates."""
        taxonomy = Taxonomy.create(
            db=db,
            data={
                "fides_key": "sensitivity",
                "name": "Sensitivity",
                "applies_to": ["data_categories"],
            },
        )

        assert "data_categories" in taxonomy.applies_to
        assert len(taxonomy.applies_to) == 1

        # Duplicate update – should be idempotent
        taxonomy.update(db=db, data={"applies_to": ["data_categories"]})
        db.flush()

        assert "data_categories" in taxonomy.applies_to
        assert len(taxonomy.applies_to) == 1

    def test_prevent_deleting_parent_element_with_children(self, db: Session):
        """Deleting a parent element with children raises an IntegrityError due to RESTRICT."""
        taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )
        parent = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "medium",
                "name": "Medium",
                "taxonomy_type": taxonomy.fides_key,
            },
        )
        TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "medium.child",
                "name": "Medium Child",
                "taxonomy_type": taxonomy.fides_key,
                "parent_key": parent.fides_key,
            },
        )
        # Attempt to delete parent should fail
        db.delete(parent)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

    def test_usage_prevents_removing_applies_to_when_in_use(self, db: Session):
        """Removing an applies_to entry that is in use raises an error."""
        # Create source taxonomy (sensitivity) that can apply to legacy data categories
        source_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )

        # Allow sensitivity to apply to data_categories
        source_taxonomy.update(db=db, data={"applies_to": ["data_categories"]})
        db.flush()

        # Create elements
        source_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "low",
                "name": "Low",
                "taxonomy_type": source_taxonomy.fides_key,
            },
        )

        # Create usage linking the elements
        usage = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key="user.contact.email",
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy="data_categories",
        )
        db.add(usage)
        db.flush()

        # Now attempt to remove "data_categories" from applies_to, it should raise due to FK constraint
        with pytest.raises(IntegrityError):
            # Try to remove the allowed usage
            source_taxonomy.update(db=db, data={"applies_to": []})
            db.flush()
        db.rollback()

    def test_usage_allows_multiple_targets_for_source(self, db: Session):
        """The same source taxonomy element can be applied to multiple target elements."""
        # Create source taxonomy (sensitivity)
        source_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )

        # Allow sensitivity to be applied to data_categories
        source_taxonomy.update(db=db, data={"applies_to": ["data_categories"]})
        db.flush()

        # Create source element (sensitivity level)
        source_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "high",
                "name": "High",
                "taxonomy_type": source_taxonomy.fides_key,
            },
        )

        target_taxonomy_key = "data_categories"
        email_target = "user.email"
        name_target = "user.name"

        # Apply the tag to both data categories
        first_usage = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=email_target,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy_key,
        )
        second_usage = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=name_target,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy_key,
        )
        db.add_all([first_usage, second_usage])
        db.flush()

        # Both usages should exist without conflict
        assert (
            db.query(TaxonomyUsage)
            .filter_by(source_element_key=source_element.fides_key)
            .count()
            == 2
        )

    def test_remove_applies_to_succeeds_when_unused(self, db: Session):
        """Removing an applies_to entry with no usages should succeed and be reflected."""
        taxonomy = Taxonomy.create(
            db=db,
            data={
                "fides_key": "sensitivity",
                "name": "Sensitivity",
                "applies_to": ["data_categories"],
            },
        )

        # No usages exist, so removal should succeed
        taxonomy.update(db=db, data={"applies_to": []})
        db.flush()
        db.refresh(taxonomy)
        assert taxonomy.applies_to == []

        # Re-add data_categories and verify
        taxonomy.update(db=db, data={"applies_to": ["data_categories"]})
        db.flush()
        db.refresh(taxonomy)
        assert taxonomy.applies_to == ["data_categories"]

    def test_create_element_hierarchy_for_sensitivity(self, db: Session):
        """Parent/child relationships on `TaxonomyElement` work for sensitivity elements."""
        taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )

        parent = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "high",
                "name": "High",
                "taxonomy_type": taxonomy.fides_key,
            },
        )

        child = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "high.child",
                "name": "High Child",
                "taxonomy_type": taxonomy.fides_key,
                "parent_key": parent.fides_key,
            },
        )

        # Relationship assertions
        assert child.parent.fides_key == parent.fides_key
        assert parent.children[0].fides_key == child.fides_key

        # Deleting the taxonomy should cascade-delete its elements
        taxonomy.delete(db)
        assert (
            db.query(TaxonomyElement)
            .filter_by(taxonomy_type=taxonomy.fides_key)
            .count()
            == 0
        )

    def test_create_element_requires_existing_parent(self, db: Session):
        """Creating an element with a non-existent parent fails due to FK constraint."""
        taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )

        with pytest.raises(IntegrityError):
            TaxonomyElement.create(
                db=db,
                data={
                    "fides_key": "medium.child",
                    "name": "Medium Child",
                    "taxonomy_type": taxonomy.fides_key,
                    "parent_key": "does.not.exist",
                },
            )

    def test_usage_enforces_uniqueness_per_source_target(self, db: Session):
        """Unique constraint on `TaxonomyUsage` prevents duplicate source->target pairs."""
        # Create taxonomies
        source_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )

        target_taxonomy_key = "data_categories"
        target_taxonomy_element_key = "user.name"

        # Allow sensitivity to be applied to data categories
        source_taxonomy.update(db=db, data={"applies_to": ["data_categories"]})
        db.flush()

        # Create elements
        source_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "medium",
                "name": "Medium",
                "taxonomy_type": source_taxonomy.fides_key,
            },
        )

        # Create first usage
        usage = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=target_taxonomy_element_key,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy_key,
        )
        db.add(usage)
        db.flush()

        # Attempt to create a duplicate usage (should fail on unique constraint)
        duplicate = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=target_taxonomy_element_key,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy_key,
        )
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

    def test_usage_supports_element_to_element_mapping(self, db: Session):
        """Taxonomy elements can be applied to other new taxonomy elements (no legacy linkage)."""
        # Create source taxonomy (sensitivity)
        source_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )

        # Create target taxonomy (impact)
        target_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "impact", "name": "Impact"},
        )

        # Allow sensitivity to be applied to impact taxonomy
        source_taxonomy.update(db=db, data={"applies_to": [target_taxonomy.fides_key]})
        db.flush()

        # Create source element (sensitivity level)
        source_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "low",
                "name": "Low",
                "taxonomy_type": source_taxonomy.fides_key,
            },
        )

        # Create target element within the new taxonomy
        target_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "impact.severe",
                "name": "Severe",
                "taxonomy_type": target_taxonomy.fides_key,
            },
        )

        # Create a TaxonomyUsage linking the new taxonomy elements
        usage = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=target_element.fides_key,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy.fides_key,
        )
        db.add(usage)
        db.flush()

        # Verify the usage was created successfully
        retrieved_usage = (
            db.query(TaxonomyUsage)
            .filter(
                TaxonomyUsage.source_element_key == source_element.fides_key,
                TaxonomyUsage.target_element_key == target_element.fides_key,
            )
            .first()
        )

        assert retrieved_usage is not None

        # Verify stored keys
        assert retrieved_usage.source_element_key == source_element.fides_key
        assert retrieved_usage.target_element_key == target_element.fides_key

    def test_usage_requires_allowed_usage(self, db: Session):
        """Creating a TaxonomyUsage fails if there is no corresponding TaxonomyAllowedUsage."""
        # Create source taxonomy but DO NOT set applies_to
        source_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "sensitivity", "name": "Sensitivity"},
        )

        # Create a source element under the source taxonomy
        source_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "low",
                "name": "Low",
                "taxonomy_type": source_taxonomy.fides_key,
            },
        )

        # Attempt to create usage without allowed usage (applies_to) should fail
        usage = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key="user.email",
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy="data_categories",
        )
        db.add(usage)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
