"""
Contains api endpoints for fides web pages
"""
from fastapi.responses import HTMLResponse

from fides.api.ctl.routes.crud import list_resource  # type: ignore[attr-defined]
from fides.api.ctl.sql_models import Evaluation  # type: ignore[attr-defined]
from fides.api.ctl.utils.api_router import APIRouter

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
    html += "<tr><th>Id</th><th>Status</th><th>Violations</th><th>Message</th></tr>"
    for evaluation in await list_resource(Evaluation):
        html += "<tr>"
        html += f"<td>{evaluation.fides_key}</td>"
        html += f"<td>{evaluation.status}</td>"

        html += "<td>"
        for index, violation in enumerate(evaluation.violations):
            violating_attributes = violation.get("violating_attributes")
            html += f"<b>Violation {index + 1}</b><br/>"
            html += "<ul>"
            html += f"<li>Data Categories: {violating_attributes.get('data_categories')}</li>"
            html += (
                f"<li>Data Subjects: {violating_attributes.get('data_subjects')}</li>"
            )
            html += f"<li>Data Uses: {violating_attributes.get('data_uses')}</li>"
            html += (
                f"<li>Data Qualifier: {violating_attributes.get('data_qualifier')}</li>"
            )
            html += f"<li>Detail: {violation.get('detail')}</li>"
            html += "</ul>"
        html += "</td>"

        html += f"<td>{evaluation.message}</td>"
        html += "</tr>"
    html += "</table>"
    html += "</head>"
    html += "</html>"
    return HTMLResponse(html)
