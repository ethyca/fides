"""
Author: Brenton Mallen
Email: brenton@ethyca.com
Company: Ethyca Data Inc.
Created: 10/5/21
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fidesctl.core import visualize

router = APIRouter()


@router.get('/categories_figure/{fig_type}')
async def get_categories_figure(fig_type: str):
    if fig_type not in ['sankey', 'sunburst', 'text']:
        return HTTPException(status_code=400,
                             detail=f'{fig_type} is not a valid figure type. Valid options: [sankey, sunburst, text]')
    # TODO make this path dynamic
    TAXONOMY_PATH = './default_taxonomy'
    if fig_type == 'sunburst':
        figure = visualize.category_sunburst_plot(TAXONOMY_PATH)
    elif fig_type == 'sankey':
        figure = visualize.category_sankey_plot(TAXONOMY_PATH)
    else:
        figure = visualize.nested_categories_to_html_list(TAXONOMY_PATH)
    return HTMLResponse(figure)
