from typing import List

from loguru import logger
from sqlalchemy import not_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import Select

from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.util import errors

AC_PREFIX = "gacp."
GVL_PREFIX = "gvl."


def exclude_gvl_systems(query: Select) -> Select:
    """Utility function to add a query clause that excludes GVL systems"""
    return query.where(
        or_(System.vendor_id.is_(None), not_(System.vendor_id.startswith(GVL_PREFIX)))
    )


def exclude_ac_systems(query: Select) -> Select:
    """Utility function to add a query clause that excludes AC systems"""
    return query.where(
        or_(System.vendor_id.is_(None), not_(System.vendor_id.startswith(AC_PREFIX)))
    )


def list_non_tcf_systems(exclude_gvl: bool = True, exclude_ac: bool = True) -> Select:
    """
    Utility to retrieve all Systems that are not GVL systems using
    the provided (async) DB session.
    """

    query = select(System)
    if exclude_gvl:
        query = exclude_gvl_systems(query)
    if exclude_ac:
        query = exclude_ac_systems(query)
    return query
