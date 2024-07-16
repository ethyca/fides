import pytest
from sqlalchemy.orm import Session

from fides.api.models.sql_models import System
from fides.api.schemas.filter_params import FilterParams
from fides.api.util.filter_utils import MissingTaxonomyField, apply_filters_to_query


class TestApplyFiltersToQuery:
    """
    Most of the logic in apply_filters_to_query is already tested through
    the tests of the endpoints that use it (e.g list systems, list datasets).
    These tests focus on the edge cases that are not covered by the other test cases.
    """

    def test_does_not_apply_filters_if_no_taxonomy_model(
        self, db: Session, system_with_cleanup, tcf_system
    ):
        query = db.query(System)
        filter_params = FilterParams(data_categories=["user.device.cookie_id"])

        filtered_query = apply_filters_to_query(
            query=query,
            filter_params=filter_params,
            search_model=System,
            taxonomy_model=None,
        )

        # tcf_system has the data_category "user.device.cookie_id", while system_with_cleanup doesn't
        # since the taxonomy_model isn't provided, we expect the query to return all systems
        query_results = db.execute(filtered_query)
        assert len(query_results.all()) == 2  # Should have both systems

    def test_raises_exception_if_taxonomy_field_is_not_in_taxonomy_model(
        self, db: Session, tcf_system
    ):
        with pytest.raises(MissingTaxonomyField) as exc:
            query = db.query(System)
            filter_params = FilterParams(data_categories=["user.device.cookie_id"])

            apply_filters_to_query(
                query=query,
                filter_params=filter_params,
                search_model=System,
                taxonomy_model=System,
            )

        assert (
            str(exc.value)
            == "Model System does not have a data_category or data_categories field, but filter_params.data_categories is not empty"
        )
