import json
import os
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2
from jinja2 import Environment, FileSystemLoader

from fides.api.models.policy import ActionType
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.redis_cache import Identity

DSR_DIRECTORY = os.path.dirname(__file__)


# pylint: disable=too-many-instance-attributes
class DsrReportBuilder:
    def __init__(
        self,
        folder_name: str,
        privacy_request: PrivacyRequest,
        dsr_data: Dict[str, Any],
    ):
        """
        Manages populating HTML templates from the given data and adding the generated
        pages to a zip file in a way that the pages can be navigated between.
        """

        # zip file variables
        self.folder_name = folder_name
        self.baos = BytesIO()

        # we close this in the finally block of generate()
        # pylint: disable=consider-using-with
        self.out = zipfile.ZipFile(self.baos, "w")

        # Jinja template environment initialization
        def pretty_print(value: str, indent: int = 4) -> str:
            return json.dumps(value, indent=indent)

        jinja2.filters.FILTERS["pretty_print"] = pretty_print
        self.template_loader = Environment(loader=FileSystemLoader(DSR_DIRECTORY))

        # to pass in custom colors in the future
        self.template_data: Dict[str, Any] = {
            "text_color": "#4A5568",
            "header_color": "#F7FAFC",
            "border_color": "#E2E8F0",
        }
        self.main_links: Dict[str, Any] = {}  # used to track the generated pages

        # report data to populate the templates
        self.request_data = _map_privacy_request(privacy_request)
        self.dsr_data = dsr_data

    def populate_template(
        self,
        template_path: str,
        heading: Optional[str] = None,
        description: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generates a file from the template and data"""
        report_data = {
            "heading": heading,
            "description": description,
            "data": data,
            "request": self.request_data,
        }
        report_data.update(self.template_data)
        template = self.template_loader.get_template(template_path)
        return template.render(report_data)

    def add_file(self, filename: str, contents: str) -> None:
        """Helper to add a file to the zip archive"""
        if filename and contents:
            self.out.writestr(f"{self.folder_name}{filename}", contents.encode("utf-8"))

    def add_dataset(self, dataset_name: str, collections: Dict[str, Any]) -> None:
        """
        Generates a page for each collection in the dataset and an index page for the dataset.
        Tracks the generated links to build a root level index after each collection has been processed.
        """
        # track links to collection indexes
        collection_links = {}
        for collection_name, rows in collections.items():
            collection_url = f"{collection_name}/index.html"
            self.add_collection(rows, dataset_name, collection_name)
            collection_links[collection_name] = collection_url

        # generate dataset index page
        self.add_file(
            f"/{dataset_name}/index.html",
            self.populate_template(
                "templates/dataset_index.html.jinja",
                dataset_name,
                None,
                collection_links,
            ),
        )

    def add_collection(
        self, rows: List[Dict[str, Any]], dataset_name: str, collection_name: str
    ) -> None:
        # track links to detail pages
        detail_links = {}
        for index, item in enumerate(rows, 1):
            detail_url = f"{index}.html"
            self.add_file(
                f"/{dataset_name}/{collection_name}/{index}.html",
                self.populate_template(
                    "templates/item.html.jinja",
                    f"{collection_name} (item #{index})",
                    None,
                    item,
                ),
            )
            detail_links[f"item #{index}"] = detail_url

        # generate detail index page
        self.add_file(
            f"/{dataset_name}/{collection_name}/index.html",
            self.populate_template(
                "templates/collection_index.html.jinja",
                collection_name,
                None,
                detail_links,
            ),
        )

    def generate(self) -> BytesIO:
        """
        Processes the request and DSR data to build zip file containing the DSR report.
        Returns the zip file as an in-memory byte array.
        """
        try:
            # all the css for the pages is in main.css
            self.add_file(
                "/main.css",
                self.populate_template("templates/main.css.jinja"),
            )
            self.add_file(
                "/logo.svg",
                Path(os.path.join(DSR_DIRECTORY, "./assets/logo.svg")).read_text(
                    encoding="utf-8"
                ),
            )
            self.add_file(
                "/back.svg",
                Path(os.path.join(DSR_DIRECTORY, "./assets/back.svg")).read_text(
                    encoding="utf-8"
                ),
            )

            # pre-process data to split the dataset:collection keys
            datasets: Dict[str, Any] = defaultdict(lambda: defaultdict(list))
            for key, rows in self.dsr_data.items():
                [dataset_name, collection_name] = key.split(":")
                datasets[dataset_name][collection_name].extend(rows)

            for dataset_name, collections in datasets.items():
                self.add_dataset(dataset_name, collections)
                self.main_links[dataset_name] = f"{dataset_name}/index.html"

            # create the main index once all the datasets have been added
            self.add_file(
                "/index.html",
                self.populate_template(
                    "templates/index.html.jinja", "DSR Report", None, self.main_links
                ),
            )
        finally:
            # close out zip file in the finally block to always close, even when an exception occurs
            self.out.close()

        # reset the file pointer so the file can be fully read by the caller
        self.baos.seek(0)
        return self.baos


def _map_privacy_request(privacy_request: PrivacyRequest) -> Dict[str, Any]:
    """Creates a map with a subset of values from the privacy request"""
    request_data = {}
    request_data["id"] = privacy_request.id
    action_type: Optional[ActionType] = privacy_request.policy.get_action_type()
    if action_type:
        request_data["type"] = action_type.value
    identity: Identity = privacy_request.get_persisted_identity()
    if identity.email:
        request_data["email"] = identity.email
    if privacy_request.requested_at:
        request_data["requested_at"] = privacy_request.requested_at.strftime(
            "%m/%d/%Y %H:%M %Z"
        )
    return request_data
