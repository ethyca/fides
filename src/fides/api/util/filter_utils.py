from typing import List, Optional, Type

from sqlalchemy import and_, func, or_
from sqlalchemy.sql.elements import BooleanClauseList
from sqlalchemy.sql.selectable import Select

from fides.api.models.sql_models import FidesBase  # type: ignore[attr-defined]
from fides.api.schemas.filter_params import FilterParams


# FIXME: this code is basically the same as the one in filter_datamap_query
# in the fidesplus repo, but slightly more generic. Ideally we want to replace that with using this
# so we don't duplicate this logic in two different places
def filter_query_by_filter_params(
    query: Select,
    filter_params: FilterParams,
    search_model: Type[FidesBase],  # Model to search on
    taxonomy_model: Optional[
        Type[FidesBase]
    ],  # Model that has the taxonomy fields to filter on
) -> Select:
    """
    Function to filter a given query by given filter params.
    The search term is used as a filter on the search_model name and fides_key, as well as its id.
    Taxonomy filters are applied to the taxonomy_model if provided.
    The search_model and taxonomy_model may be the same model, e.g if the lookup is on one table,
    or may be different, e.g if the query is performing a join between two tables.
    Returns the filtered query.
    """
    if filter_params.search:
        query = query.where(
            and_(
                or_(
                    func.lower(search_model.name).like(
                        f"%{filter_params.search.lower()}%"
                    ),
                    search_model.fides_key == filter_params.search,
                    search_model.id == filter_params.search,
                )
            )
        )

    if not taxonomy_model:
        return query

    taxonomy_filter_conditions: List[BooleanClauseList] = []

    if filter_params.data_uses:
        data_use_conditions = or_(
            *[
                taxonomy_model.data_use.like(data_use + "%")
                for data_use in filter_params.data_uses
            ]
        )
        taxonomy_filter_conditions.append(data_use_conditions)

    if filter_params.data_categories:
        data_categories_conditions = or_(
            *[
                taxonomy_model.data_categories.contains([data_category])
                for data_category in filter_params.data_categories
            ]
        )
        taxonomy_filter_conditions.append(data_categories_conditions)

    if filter_params.data_subjects:
        data_subjects_conditions = or_(
            *[
                taxonomy_model.data_subjects.contains([data_subject])
                for data_subject in filter_params.data_subjects
            ]
        )
        taxonomy_filter_conditions.append(data_subjects_conditions)

    # filter the query for taxonomy_model instances that match the filter params
    if taxonomy_filter_conditions:
        query = query.where(and_(*taxonomy_filter_conditions))

    return query
