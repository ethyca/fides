"""
api endpoint for category visualisation
"""
from enum import Enum
from typing import Union

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from fidesctl.core import visualize
from fideslang import DEFAULT_TAXONOMY, model_map


VISUALIZABLE_RESOURCE_TYPES = ["data_category", "data_qualifier", "data_use"]


class FigureTypeEnum(str, Enum):
    "The model for possible evaluation results."

    SANKEY = "sankey"
    SUNBURST = "sunburst"
    TEXT = "text"


def get_resource_type(router: APIRouter) -> str:
    "Extracts the name of the resource type from the prefix."
    return router.prefix[1:]


routers = []
for resource_type in VISUALIZABLE_RESOURCE_TYPES:
    # Programmatically define routers for each resource type
    resource_model_name = model_map[resource_type].__name__
    router = APIRouter(
        tags=["Visualize", resource_model_name],
        prefix=f"/{resource_type}",
    )

    @router.get("/visualize/{figure_type}")
    async def get_visualization(
        figure_type: FigureTypeEnum, resource_type: str = get_resource_type(router)
    ) -> Union[HTMLResponse, HTTPException]:
        """
        Visualize the hierarchy of a supported resource type.
        """
        if figure_type not in ["sankey", "sunburst", "text"]:
            return HTTPException(
                status_code=400,
                detail=f"{figure_type} is not a valid figure type. Valid options: [sankey, sunburst, text]",
            )
        taxonomy = DEFAULT_TAXONOMY.dict()[resource_type]
        if figure_type == "sunburst":
            figure = visualize.category_sunburst_plot(taxonomy)
        elif figure_type == "sankey":
            figure = visualize.category_sankey_plot(taxonomy)
        else:
            figure = visualize.nested_categories_to_html_list(taxonomy)
        return HTMLResponse(figure)

    routers += [router]
