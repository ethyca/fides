"""
API endpoints for displaying hierarchical data representations.
"""
from enum import Enum
from typing import Union

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from fidesapi.crud import list_resource
from fidesapi.sql_models import sql_model_map
from fidesctl.core import visualize
from fideslang import model_map

# pylint: disable=redefined-outer-name,cell-var-from-loop

VISUALIZABLE_RESOURCE_TYPES = ["data_category", "data_qualifier", "data_use"]


class FigureTypeEnum(str, Enum):
    """
    Figure Type Enum to capture the discrete possible values
    for a valid figure type to be visualized
    """

    GRAPHS = "graphs"
    TEXT = "text"


def get_resource_type(router: APIRouter) -> str:
    """
    Get the resource type from the prefix of an API router
    Args:
        router: Api router from which to extract the resource type

    Returns:
        The router's resource type
    """
    return router.prefix[1:]


routers = []
for resource_type in VISUALIZABLE_RESOURCE_TYPES:
    # Programmatically define routers for each resource type
    RESOURCE_MODEL_NAME = model_map[resource_type].__name__
    router = APIRouter(
        tags=["Visualize", RESOURCE_MODEL_NAME],
        prefix=f"/{resource_type}",
    )

    @router.get("/visualize/{figure_type}")
    async def get_chart(
        figure_type: FigureTypeEnum, resource_type: str = get_resource_type(router)
    ) -> Union[HTMLResponse, HTTPException]:
        """
            Visualize the hierarchy of a supported resource type.
        Args:
            figure_type: type of figure, by name, to generate
            resource_type: hierarchy source. one of ["data_category", "data_qualifier", "data_use"]
        Returns:
            Html for the requested figure. Response with status code 400 when invalid figure type is provided
        """
        sql_model = sql_model_map[resource_type]
        resource_object_list = list_resource(sql_model)
        resource_list = [resource.__dict__ for resource in resource_object_list]
        if figure_type == "text":
            figure = visualize.nested_categories_to_html_list(
                resource_list, resource_type
            )
        else:
            figure = visualize.hierarchy_figures(resource_list, resource_type)
        return HTMLResponse(figure)

    routers += [router]
