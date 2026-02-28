"""
Contains api endpoints for fides web pages
"""

from fastapi import Depends, Security
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.db.crud import list_resource
from fides.api.db.ctl_session import get_async_db
from fides.api.models.sql_models import Evaluation  # type: ignore[attr-defined]
from fides.api.oauth.utils import verify_oauth_client_prod
from fides.api.util.api_router import APIRouter
from fides.common.api import scope_registry

router = APIRouter(
    tags=["View"],
    prefix="/view",
)


@router.get(
    "/evaluations",
    dependencies=[
        Security(verify_oauth_client_prod, scopes=[scope_registry.EVALUATION_READ])
    ],
)
async def evaluation_view(db: AsyncSession = Depends(get_async_db)) -> HTMLResponse:
    "Returns an html document with a list of evaluations"

    html = '<html lang="en">'
    html += "<head>"
    html += '<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">'
    html += "<body>"
    html += "<h2>Evaluations</h2>"
    html += '<table class="table table-striped" style="text-align: left;">'
    html += "<tr><th>Id</th><th>Status</th><th>Violations</th><th>Message</th></tr>"
    for evaluation in await list_resource(Evaluation, db):
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
            html += f"<li>Detail: {violation.get('detail')}</li>"
            html += "</ul>"
        html += "</td>"

        html += f"<td>{evaluation.message}</td>"
        html += "</tr>"
    html += "</table>"
    html += "</head>"
    html += "</html>"
    return HTMLResponse(html)
