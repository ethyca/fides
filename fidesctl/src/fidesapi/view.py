"""
Contains api endpoints for fides web pages
"""
from fastapi import APIRouter

from fidesapi.crud import list_resource
from fidesapi.sql_models import Evaluation
from fastapi.responses import HTMLResponse

router = APIRouter(
    tags=["View"],
    prefix=f"/view",
)

@router.get("/evaluations")
async def evaluation_view() -> HTMLResponse:
    "Returns an html document with a list of evaluations"

    html = f'<h2>Fidesctl Evaluations</h2>'
    html += f'<table style="text-align: left;">'
    html += f'<tr><th>Id</th><th>Status</th><th>Details</th><th>Message</th></tr>'
    for evaluation in list_resource(Evaluation):
        html += f'<tr>'
        html += f'<td><div style="width: 400px;">{evaluation.fides_key}</div></td>';
        html += f'<td><div style="width: 50px;">{evaluation.status}</div></td>';

        html += f'<td><div style="width: 500px;">';
        for detail in evaluation.details:
            html += f'{detail}<br/>';
        html += f'</div></td>';
        
        html += f'<td><div style="width: 500px;">{evaluation.message}</div></td>';
        html += f'</tr>'
    html += f'</table>'
    return HTMLResponse(html)
