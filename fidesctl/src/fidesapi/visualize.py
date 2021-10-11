"""
API endpoints for displaying hierarchical data representations.
"""
from enum import Enum
from typing import Union

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from fidesctl.core import visualize
from fideslang import DEFAULT_TAXONOMY, model_map

# pylint: disable=redefined-outer-name,cell-var-from-loop

VISUALIZABLE_RESOURCE_TYPES = ["data_category", "data_qualifier", "data_use"]


class FigureTypeEnum(str, Enum):
    """
    Figure Type Enum to capture the discrete possible values
    for a valid figure type to be visualized
    """

    SANKEY = "sankey"
    SUNBURST = "sunburst"
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
    async def get_visualization(
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
        if figure_type not in ["sankey", "sunburst", "text"]:
            return HTTPException(
                status_code=400,
                detail=f"{figure_type} is not a valid figure type. Valid options: [sankey, sunburst, text]",
            )
        taxonomy = DEFAULT_TAXONOMY.dict()[resource_type]
        if figure_type == "sunburst":
            figure = visualize.sunburst_plot(taxonomy, resource_type)
        elif figure_type == "sankey":
            figure = visualize.sankey_plot(taxonomy, resource_type)
        else:
            figure = visualize.nested_categories_to_html_list(taxonomy, resource_type)
        return HTMLResponse(figure)

    routers += [router]
