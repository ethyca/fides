import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.taxonomy import (
    TargetType,
    Taxonomy,
    TaxonomyElement,
    TaxonomyUsage,
)


class TestTaxonomyModels:
    def test_taxonomy_add_applies_to_idempotent(self, db: Session):
        """Setting the same target type twice should not create duplicates."""
        taxonomy = Taxonomy.create(
            db=db,
            data={
                "fides_key": "idempotent_tax",
                "name": "Idempotent Tax",
                "applies_to": [TargetType.SYSTEM.value],
            },
        )

        assert TargetType.SYSTEM.value in taxonomy.applies_to
        assert len(taxonomy.applies_to) == 1

        # Duplicate update – should be idempotent
        taxonomy.update(db=db, data={"applies_to": [TargetType.SYSTEM.value]})
        db.flush()

        assert TargetType.SYSTEM.value in taxonomy.applies_to
        assert len(taxonomy.applies_to) == 1

    def test_taxonomy_can_apply_to_generic_target_types(self, db: Session):
        """Test that taxonomy can apply to generic types like SYSTEM."""
        taxonomy = Taxonomy.create(
            db=db,
            data={
                "fides_key": "generic_check_tax",
                "name": "Generic Check Tax",
                "applies_to": [TargetType.SYSTEM.value],
            },
        )

        # Verify the value was added
        assert TargetType.SYSTEM.value in taxonomy.applies_to

    # ------------------------------------------------------------------
    # TaxonomyElement parent/child delete behavior
    # ------------------------------------------------------------------

    def test_parent_element_delete_restricted_if_children_exist(self, db: Session):
        """Deleting a parent element with children should raise an IntegrityError due to RESTRICT."""
        taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "delete_restrict_tax", "name": "Delete Restrict Tax"},
        )
        parent = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "restrict_parent",
                "name": "Restrict Parent",
                "taxonomy_type": taxonomy.fides_key,
            },
        )
        TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "restrict_child",
                "name": "Restrict Child",
                "taxonomy_type": taxonomy.fides_key,
                "parent_key": parent.fides_key,
            },
        )
        # Attempt to delete parent should fail
        db.delete(parent)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

    # ------------------------------------------------------------------
    # applies_to removal behavior
    # ------------------------------------------------------------------

    def test_remove_applies_to_with_existing_usage(self, db: Session):
        """Attempting to remove an `applies_to` entry that is in use should raise an error."""
        # Create source taxonomy that can apply to target taxonomy
        source_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "tags", "name": "Tags"},
        )

        target_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "categories", "name": "Categories"},
        )

        # Allow tags to apply to categories
        source_taxonomy.update(db=db, data={"applies_to": ["categories"]})
        db.flush()

        # Create elements
        source_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "tag1",
                "name": "Tag 1",
                "taxonomy_type": source_taxonomy.fides_key,
            },
        )

        target_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "cat1",
                "name": "Category 1",
                "taxonomy_type": target_taxonomy.fides_key,
            },
        )

        # Create usage linking the elements
        usage = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=target_element.fides_key,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy.fides_key,
        )
        db.add(usage)
        db.flush()

        # Now attempt to remove "categories" from applies_to – should raise due to FK constraint
        with pytest.raises(IntegrityError):
            # Try to remove the allowed usage
            source_taxonomy.update(db=db, data={"applies_to": []})
            db.flush()
        db.rollback()

    # ------------------------------------------------------------------
    # TaxonomyUsage behavior
    # ------------------------------------------------------------------

    def test_taxonomy_usage_allows_multiple_targets(self, db: Session):
        """The same taxonomy element can be applied to different target elements."""
        # Create source taxonomy (e.g., custom tags)
        source_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "custom_tags", "name": "Custom Tags"},
        )

        # Create target taxonomy (e.g., data categories)
        target_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "data_categories", "name": "Data Categories"},
        )

        # Allow custom_tags to be applied to data_categories
        source_taxonomy.update(db=db, data={"applies_to": ["data_categories"]})
        db.flush()

        # Create source element (a custom tag)
        source_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "pii_tag",
                "name": "PII Tag",
                "taxonomy_type": source_taxonomy.fides_key,
            },
        )

        # Create target elements (data categories)
        target1 = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "user.email",
                "name": "User Email",
                "taxonomy_type": target_taxonomy.fides_key,
            },
        )
        target2 = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "user.name",
                "name": "User Name",
                "taxonomy_type": target_taxonomy.fides_key,
            },
        )

        # Apply the tag to both data categories
        usage1 = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=target1.fides_key,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy.fides_key,
        )
        usage2 = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=target2.fides_key,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy.fides_key,
        )
        db.add_all([usage1, usage2])
        db.flush()

        # Both usages should exist without conflict
        assert (
            db.query(TaxonomyUsage)
            .filter_by(source_element_key=source_element.fides_key)
            .count()
            == 2
        )

    # ------------------------------------------------------------------
    # Combined helper behavior scenario
    # ------------------------------------------------------------------

    def test_taxonomy_create_and_apply_to_helpers(self, db: Session):
        """Verify `Taxonomy.create` works and that `applies_to` property behaves as expected."""
        taxonomy = Taxonomy.create(
            db=db,
            data={
                "fides_key": "test_taxonomy",
                "name": "Test Taxonomy",
                "applies_to": [TargetType.SYSTEM.value],
            },
        )

        # Should now apply to SYSTEM but not DATASET yet
        assert TargetType.SYSTEM.value in taxonomy.applies_to
        assert TargetType.DATASET.value not in taxonomy.applies_to

        # Add applies_to for DATASET
        taxonomy.update(
            db=db,
            data={"applies_to": [TargetType.SYSTEM.value, TargetType.DATASET.value]},
        )
        db.flush()
        db.refresh(taxonomy)
        assert TargetType.DATASET.value in taxonomy.applies_to

        # Remove SYSTEM and verify response
        taxonomy.update(db=db, data={"applies_to": [TargetType.DATASET.value]})
        db.flush()
        db.refresh(taxonomy)
        assert TargetType.SYSTEM.value not in taxonomy.applies_to

        # Add a taxonomy-to-taxonomy relationship and check helper logic
        other_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "other_tax", "name": "Other Taxonomy"},
        )
        # Add other_taxonomy to the list
        taxonomy.update(
            db=db,
            data={"applies_to": [TargetType.DATASET.value, other_taxonomy.fides_key]},
        )
        db.flush()
        db.refresh(taxonomy)
        assert other_taxonomy.fides_key in taxonomy.applies_to

    # ------------------------------------------------------------------
    # TaxonomyElement hierarchy tests
    # ------------------------------------------------------------------

    def test_taxonomy_element_hierarchy(self, db: Session):
        """Verify parent/child relationships on `TaxonomyElement` work as expected."""
        taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "hierarchy_tax", "name": "Hierarchy Tax"},
        )

        parent = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "parent_element",
                "name": "Parent Element",
                "taxonomy_type": taxonomy.fides_key,
            },
        )

        child = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "child_element",
                "name": "Child Element",
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

    # ------------------------------------------------------------------
    # TaxonomyUsage uniqueness constraint
    # ------------------------------------------------------------------

    def test_taxonomy_usage_unique_constraint(self, db: Session):
        """Ensure the unique constraint on `TaxonomyUsage` is enforced."""
        # Create taxonomies
        source_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "tags", "name": "Tags"},
        )
        target_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "categories", "name": "Categories"},
        )

        # Allow tags to be applied to categories
        source_taxonomy.update(db=db, data={"applies_to": ["categories"]})
        db.flush()

        # Create elements
        source_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "sensitive",
                "name": "Sensitive",
                "taxonomy_type": source_taxonomy.fides_key,
            },
        )
        target_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "personal",
                "name": "Personal",
                "taxonomy_type": target_taxonomy.fides_key,
            },
        )

        # Create first usage
        usage = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=target_element.fides_key,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy.fides_key,
        )
        db.add(usage)
        db.flush()

        # Attempt to create a duplicate usage (should fail on unique constraint)
        duplicate = TaxonomyUsage(
            source_element_key=source_element.fides_key,
            target_element_key=target_element.fides_key,
            source_taxonomy=source_taxonomy.fides_key,
            target_taxonomy=target_taxonomy.fides_key,
        )
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

    def test_taxonomy_usage_element_to_element(self, db: Session):
        """Test that taxonomy elements can be applied to other taxonomy elements."""
        # Create source taxonomy
        source_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "custom_tags", "name": "Custom Tags"},
        )

        # Create target taxonomy (e.g., data_categories that custom_tags can be applied to)
        target_taxonomy = Taxonomy.create(
            db=db,
            data={"fides_key": "data_categories", "name": "Data Categories"},
        )

        # Allow custom_tags to be applied to data_categories taxonomy
        source_taxonomy.update(db=db, data={"applies_to": ["data_categories"]})
        db.flush()

        # Create source element (a custom tag)
        source_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "custom_tag_1",
                "name": "Custom Tag 1",
                "taxonomy_type": source_taxonomy.fides_key,
            },
        )

        # Create target element (a data category)
        target_element = TaxonomyElement.create(
            db=db,
            data={
                "fides_key": "user.contact",
                "name": "User Contact",
                "taxonomy_type": target_taxonomy.fides_key,
            },
        )

        # Create a TaxonomyUsage linking the elements
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
        assert retrieved_usage.source_taxonomy == source_taxonomy.fides_key
        assert retrieved_usage.target_taxonomy == target_taxonomy.fides_key

        # Verify relationships work
        assert retrieved_usage.source_element.fides_key == source_element.fides_key
        assert retrieved_usage.target_element.fides_key == target_element.fides_key
