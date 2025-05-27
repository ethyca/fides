import json
import os
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jinja2
from jinja2 import Environment, FileSystemLoader

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.util.storage_util import StorageJSONEncoder

DSR_DIRECTORY = Path(__file__).parent.resolve()

TEXT_COLOR = "#4A5568"
HEADER_COLOR = "#FAFAFA"
BORDER_COLOR = "#E2E8F0"


# pylint: disable=too-many-instance-attributes
class DsrReportBuilder:
    def __init__(
        self,
        privacy_request: PrivacyRequest,
        dsr_data: Dict[str, Any],
    ):
        """
        Manages populating HTML templates from the given data and adding the generated
        pages to a zip file in a way that the pages can be navigated between.
        """

        # zip file variables
        self.baos = BytesIO()

        # we close this in the finally block of generate()
        # pylint: disable=consider-using-with
        self.out = zipfile.ZipFile(self.baos, "w")

        # Jinja template environment initialization
        def pretty_print(value: str, indent: int = 4) -> str:
            return json.dumps(value, indent=indent, cls=StorageJSONEncoder)

        jinja2.filters.FILTERS["pretty_print"] = pretty_print
        self.template_loader = Environment(
            loader=FileSystemLoader(DSR_DIRECTORY), autoescape=True
        )

        # to pass in custom colors in the future
        self.template_data: Dict[str, Any] = {
            "text_color": TEXT_COLOR,
            "header_color": HEADER_COLOR,
            "border_color": BORDER_COLOR,
        }
        self.main_links: Dict[str, Any] = {}  # used to track the generated pages

        # report data to populate the templates
        self.request_data = _map_privacy_request(privacy_request)
        self.dsr_data = dsr_data

    def _populate_template(
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
        rendered_template = template.render(report_data)
        return rendered_template

    def _add_file(self, filename: str, contents: str) -> None:
        """Helper to add a file to the zip archive"""
        if filename and contents:
            self.out.writestr(f"{filename}", contents.encode("utf-8"))

    def _add_dataset(self, dataset_name: str, collections: Dict[str, Any]) -> None:
        """
        Generates a page for each collection in the dataset and an index page for the dataset.
        Tracks the generated links to build a root level index after each collection has been processed.
        """
        # track links to collection indexes
        collection_links = {}
        for collection_name, rows in collections.items():
            collection_url = f"{collection_name}/index.html"
            self._add_collection(rows, dataset_name, collection_name)
            collection_links[collection_name] = collection_url

        # generate dataset index page
        self._add_file(
            f"data/{dataset_name}/index.html",
            self._populate_template(
                "templates/dataset_index.html",
                dataset_name,
                None,
                collection_links,
            ),
        )

    def _add_collection(
        self, rows: List[Dict[str, Any]], dataset_name: str, collection_name: str
    ) -> None:
        # track links to detail pages
        detail_links = {}
        for index, item in enumerate(rows, 1):
            detail_url = f"{index}.html"

            # Handle attachments in the item if they exist
            if "attachments" in item and isinstance(item["attachments"], list):
                for attachment in item["attachments"]:
                    file_name = attachment.get("file_name", "unknown")
                    content = attachment.get("content")
                    content_type = attachment.get("content_type", "")

                    if content:
                        # Save to top-level attachments directory
                        if content_type.startswith("text/"):
                            if isinstance(content, bytes):
                                content = content.decode("utf-8")
                            self._add_file(f"attachments/{file_name}", content)
                        else:
                            if not isinstance(content, bytes):
                                content = content.encode("utf-8")
                            self.out.writestr(f"attachments/{file_name}", content)

                        # Also save to the manual webhook directory
                        if content_type.startswith("text/"):
                            self._add_file(
                                f"data/{dataset_name}/{collection_name}/{file_name}",
                                content,
                            )
                        else:
                            self.out.writestr(
                                f"data/{dataset_name}/{collection_name}/{file_name}",
                                content,
                            )

            self._add_file(
                f"data/{dataset_name}/{collection_name}/{index}.html",
                self._populate_template(
                    "templates/item.html",
                    f"{collection_name} (item #{index})",
                    None,
                    item,
                ),
            )
            detail_links[f"item #{index}"] = detail_url

        # generate detail index page
        self._add_file(
            f"data/{dataset_name}/{collection_name}/index.html",
            self._populate_template(
                "templates/collection_index.html",
                collection_name,
                None,
                detail_links,
            ),
        )

    def _add_attachments(self, attachments: List[Dict[str, Any]]) -> None:
        """
        Generates an attachments directory with an index page and adds the attachments to the zip file.
        """
        if not attachments or not isinstance(attachments, list):
            return

        # Create attachment links for the index page
        attachment_links = {}
        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue

            file_name = attachment.get("file_name", "unknown")
            content_type = attachment.get("content_type", "")
            attachment_links[file_name] = f"{file_name}"

            # Add the attachment content to the zip file
            content = attachment.get("content")
            if content:
                # For text-based files, we need to encode them
                if content_type.startswith("text/"):
                    if isinstance(content, bytes):
                        content = content.decode("utf-8")
                    self._add_file(f"attachments/{file_name}", content)
                # For binary files, write them directly
                else:
                    if not isinstance(content, bytes):
                        content = content.encode("utf-8")
                    self.out.writestr(f"attachments/{file_name}", content)

        # Generate attachments index page using the attachments index template
        self._add_file(
            "attachments/index.html",
            self._populate_template(
                "templates/attachments_index.html",
                "Attachments",
                "Files attached to this privacy request",
                attachment_links,
            ),
        )

    def _get_dataset_and_collections(
        self, key: str, rows: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Returns the dataset name for the given key and rows.
        """
        print(key)
        print(rows)
        parts = key.split(":", 1)
        if len(parts) > 1:
            return parts
        if "system_name" in rows[0]:
            return (rows[0]["system_name"], parts[0])
        return ("manual", parts[0])

    def generate(self) -> BytesIO:
        """
        Processes the request and DSR data to build zip file containing the DSR report.
        Returns the zip file as an in-memory byte array.
        """
        try:
            # all the css for the pages is in main.css
            self._add_file(
                "data/main.css",
                self._populate_template("templates/main.css"),
            )
            self._add_file(
                "data/back.svg",
                Path(os.path.join(DSR_DIRECTORY, "assets/back.svg")).read_text(
                    encoding="utf-8"
                ),
            )

            # pre-process data to split the dataset:collection keys
            datasets: Dict[str, Any] = defaultdict(lambda: defaultdict(list))
            for key, rows in self.dsr_data.items():
                if key == "attachments":
                    # Handle attachments separately
                    self._add_attachments(rows)
                    self.main_links["Additional Attachments"] = "attachments/index.html"
                    continue

                parts = key.split(":", 1)
                if len(parts) > 1:
                    dataset_name, collection_name = parts
                else:
                    for row in rows:
                        if "system_name" in row:
                            dataset_name = row["system_name"]
                            collection_name = parts[0]
                            break
                    else:
                        dataset_name = "manual"
                        collection_name = parts[0]

                datasets[dataset_name][collection_name].extend(rows)

            for dataset_name, collections in datasets.items():
                self._add_dataset(dataset_name, collections)
                self.main_links[dataset_name] = f"data/{dataset_name}/index.html"

            # create the main index once all the datasets have been added
            self._add_file(
                "welcome.html",
                self._populate_template(
                    "templates/welcome.html", "DSR Report", None, self.main_links
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
    request_data: Dict[str, Any] = {}
    request_data["id"] = privacy_request.id

    action_type: Optional[ActionType] = privacy_request.policy.get_action_type()
    if action_type:
        request_data["type"] = action_type.value

    request_data["identity"] = {
        key: value
        for key, value in privacy_request.get_persisted_identity()
        .labeled_dict(include_default_labels=True)
        .items()
        if value["value"] is not None
    }

    if privacy_request.requested_at:
        request_data["requested_at"] = privacy_request.requested_at.strftime(
            "%m/%d/%Y %H:%M %Z"
        )
    return request_data
