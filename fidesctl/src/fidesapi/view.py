"""
Contains api endpoints for fides web pages
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fidesapi.crud import list_resource
from fidesapi.sql_models import Evaluation

router = APIRouter(
    tags=["View"],
    prefix="/view",
)


@router.get("/evaluations")
async def evaluation_view() -> HTMLResponse:
    "Returns an html document with a list of evaluations"

    html = '<html lang="en">'
    html += "<head>"
    html += '<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">'
    html += "<body>"
    html += "<h2>Evaluations</h2>"
    html += '<table class="table table-striped" style="text-align: left;">'
    html += "<tr><th>Id</th><th>Status</th><th>Details</th><th>Message</th></tr>"
    for evaluation in list_resource(Evaluation):
        html += "<tr>"
        html += f"<td>{evaluation.fides_key}</td>"
        html += f"<td>{evaluation.status}</td>"

        html += "<td>"
        for detail in evaluation.details:
            html += f"{detail}<br/>"
        html += "</td>"

        html += f"<td>{evaluation.message}</td>"
        html += "</tr>"
    html += "</table>"
    html += "</head>"
    html += "</html>"
    return HTMLResponse(html)
