"""
api endpoint for category visualisation
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fidesctl.core import visualize
from fideslang.default_taxonomy import DEFAULT_TAXONOMY

router = APIRouter()

DEFAULT_CATEGORY_KEY = 'data_category'


@router.get('/categories_figure/{fig_type}')
async def get_categories_figure(fig_type: str):
    if fig_type not in ['sankey', 'sunburst', 'text']:
        return HTTPException(status_code=400,
                             detail=f'{fig_type} is not a valid figure type. Valid options: [sankey, sunburst, text]')
    taxonomy = DEFAULT_TAXONOMY.dict()[DEFAULT_CATEGORY_KEY]
    if fig_type == 'sunburst':
        figure = visualize.category_sunburst_plot(taxonomy)
    elif fig_type == 'sankey':
        figure = visualize.category_sankey_plot(taxonomy)
    else:
        figure = visualize.nested_categories_to_html_list(taxonomy)
    return HTMLResponse(figure)
