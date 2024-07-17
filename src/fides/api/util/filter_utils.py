from typing import List, Optional, Type

from sqlalchemy import and_, func, or_
from sqlalchemy.sql.elements import BooleanClauseList
from sqlalchemy.sql.selectable import Select

from fides.api.models.sql_models import FidesBase  # type: ignore[attr-defined]
from fides.api.schemas.filter_params import FilterParams


class MissingTaxonomyField(ValueError):
    pass


# FIXME: this code is basically the same as the one in filter_datamap_query
# in the fidesplus repo, but slightly more generic. Ideally we want to replace that with using this
# so we don't duplicate this logic in two different places
def apply_filters_to_query(
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

    # Perform a text search on the search_model's name, fides_key and id
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

    # We match the name of the field in FilterParams to the name of the field in the taxonomy_model,
    # which can be represented by either a single element field or a collection field
    taxonomy_field_information = {
        "data_categories": {
            "single": "data_category",
            "collection": "data_categories",
        },
        "data_subjects": {
            "single": "data_subject",
            "collection": "data_subjects",
        },
        "data_uses": {
            "single": "data_use",
            "collection": "data_uses",
        },
    }

    # Filter the fields so we only use the ones that have been provided in the filter params
    available_fields_info = {
        field: field_info
        for field, field_info in taxonomy_field_information.items()
        if getattr(filter_params, field)
    }

    taxonomy_filter_conditions: List[BooleanClauseList] = []

    for field, field_info in available_fields_info.items():
        single_field_name = field_info["single"]
        collection_field_name = field_info["collection"]

        # If the taxonomy_model doesn't have either a single or collection field matching this field
        # we raise an error since it makes no sense to pass in the field as part of the filter params
        if not hasattr(taxonomy_model, single_field_name) and not hasattr(
            taxonomy_model, collection_field_name
        ):
            raise MissingTaxonomyField(
                f"Model {taxonomy_model.__name__} does not have a {single_field_name} or {collection_field_name} field, but filter_params.{field} is not empty"
            )

        single_field_conditions = []
        collection_field_conditions = []

        # For single fields, we match each element provided in the filter params field
        # against the field in the taxonomy model using like, since model field is a single element
        # e.g a single data category represented as a string
        if hasattr(taxonomy_model, single_field_name):
            single_field_conditions = [
                getattr(taxonomy_model, single_field_name).like(element + "%")
                for element in getattr(filter_params, field)
            ]

        # For collection fields, we match each element provided in the filter params field
        # against the field in the taxonomy model using contains, since model field is
        # a collection of elements, e.g a list of data categories
        if hasattr(taxonomy_model, collection_field_name):
            collection_field_conditions = [
                getattr(taxonomy_model, collection_field_name).contains([element])
                for element in getattr(filter_params, field)
            ]

        # We join all conditions with an OR, so that we retrieve rows that match
        # either in their single or collection fields
        all_field_conditions = or_(
            *single_field_conditions, *collection_field_conditions
        )
        taxonomy_filter_conditions.append(all_field_conditions)

    # Finally, we filter the query for taxonomy_model instances that match all the conditions
    if taxonomy_filter_conditions:
        query = query.where(and_(*taxonomy_filter_conditions))

    return query
