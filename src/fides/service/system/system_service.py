import datetime
from typing import Any, List, Literal, Optional, Union

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.async_sqlalchemy import paginate as async_paginate
from fideslang.validation import FidesKey
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.selectable import Select

from fides.api.db.crud import list_resource
from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    PrivacyDeclaration,
    System,
)
from fides.api.schemas.filter_params import FilterParams
from fides.api.util.filter_utils import apply_filters_to_query


class SystemService:
    """
    Service for system management. Currently only used for listing systems.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_systems(
        self,
        *,
        search: Optional[str] = None,
        data_uses: Optional[List[FidesKey]] = None,
        data_categories: Optional[List[FidesKey]] = None,
        data_subjects: Optional[List[FidesKey]] = None,
        size: Optional[int] = None,
        page: Optional[int] = None,
        show_deleted: bool = False,
        sort_by: Optional[List[Literal["name"]]] = None,
        sort_asc: Optional[bool] = True,
        **kwargs: Any,
    ) -> Union[List[System], Page[System]]:
        """
        Query systems with flexible filtering and optional pagination.

        This function provides the core logic for listing systems with support for:
        - Basic filtering (search, data uses, categories, subjects)
        - Pagination
        - Vendor deletion filtering
        - Extension points for additional filtering

        Args:
            db: Database session
            size: Page size for pagination (if None, no pagination)
            page: Page number for pagination
            show_deleted: Whether to include vendor-deleted systems
            filter_params: Standard filter parameters (search, taxonomy filters)

        Returns:
            Either a list of all systems or a paginated page of systems
        """

        filter_params = None
        if any([search, data_uses, data_categories, data_subjects]):
            filter_params = FilterParams(
                search=search,
                data_uses=data_uses,
                data_categories=data_categories,
                data_subjects=data_subjects,
            )

        # If no parameters are provided, return all systems for backward compatibility
        if not any([size, page, filter_params]):
            return await list_resource(System, self.db)

        query = self._build_systems_query(
            filter_params=filter_params,
            show_deleted=show_deleted,
            **kwargs,
        )

        # Ensure distinct results
        if sort_by:
            for sort_column_name in sort_by:
                if sort_column_name == "name":
                    name_order = System.name.asc() if sort_asc else System.name.desc()
                    # For name sorting, we need name first in ORDER BY, then id for uniqueness
                    query = query.distinct(System.name, System.id).order_by(
                        name_order, System.id
                    )
        else:
            # Default to ascending name sort when no sorting parameters are provided
            name_order = System.name.asc()
            query = query.distinct(System.name, System.id).order_by(
                name_order, System.id
            )

        # Return paginated or non-paginated results
        if size or page:
            pagination_params = Params(page=page or 1, size=size or 50)
            return await async_paginate(self.db, query, pagination_params)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _build_systems_query(
        self,
        *,
        filter_params: Optional[FilterParams] = None,
        show_deleted: bool = False,
        **kwargs: Any,
    ) -> Select:
        """
        Build the base query for systems.
        """

        query = select(System)

        # Determine if we need to join with PrivacyDeclaration
        needs_privacy_declaration = filter_params and any(
            [
                filter_params.data_uses,
                filter_params.data_categories,
                filter_params.data_subjects,
            ]
        )

        if needs_privacy_declaration:
            query = query.outerjoin(
                PrivacyDeclaration, System.id == PrivacyDeclaration.system_id
            )

        # Filter out vendor deleted systems unless explicitly asked for
        if not show_deleted:
            query = query.filter(
                or_(
                    System.vendor_deleted_date.is_(None),
                    System.vendor_deleted_date >= datetime.datetime.now(),
                )
            )

        # Apply standard filters if provided
        if filter_params:
            query = apply_filters_to_query(
                query=query,
                filter_params=filter_params,
                search_model=System,
                taxonomy_model=(
                    PrivacyDeclaration if needs_privacy_declaration else None
                ),
            )

        return query
