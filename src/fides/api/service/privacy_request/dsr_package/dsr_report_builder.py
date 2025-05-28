import json
import os
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import jinja2
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.util.storage_util import StorageJSONEncoder

DSR_DIRECTORY = Path(__file__).parent.resolve()

TEXT_COLOR = "#4A5568"
HEADER_COLOR = "#FAFAFA"
BORDER_COLOR = "#E2E8F0"


# pylint: disable=too-many-instance-attributes
class DsrReportBuilder:
    """
    Manages populating HTML templates from the given data and adding the generated
    pages to a zip file in a way that the pages can be navigated between.

    The zip file is structured as follows:
    - welcome.html: the main index page
    - data/dataset_name/index.html: the index page for the dataset
    - data/dataset_name/collection_name/index.html: the index page for the collection
    - data/dataset_name/collection_name/item_index.html: the detail page for the item
    - attachments/index.html: the index page for the attachments
    - attachments/attachment_name: the attachment file

    Args:
        privacy_request: the privacy request object
        dsr_data: the DSR data
    """

    def __init__(
        self,
        privacy_request: PrivacyRequest,
        dsr_data: dict[str, Any],
    ):
        """
        Initializes the DSR report builder.
        """
        # Define pretty_print function for Jinja templates
        jinja2.filters.FILTERS["pretty_print"] = lambda value, indent=4: json.dumps(
            value, indent=indent, cls=StorageJSONEncoder
        )

        # Initialize instance zip file variables
        self.baos = BytesIO()

        # we close this in the finally block of generate()
        # pylint: disable=consider-using-with
        self.out = zipfile.ZipFile(self.baos, "w")
        self.template_loader = Environment(
            loader=FileSystemLoader(DSR_DIRECTORY), autoescape=True
        )
        self.template_data: dict[str, Any] = {
            "text_color": TEXT_COLOR,
            "header_color": HEADER_COLOR,
            "border_color": BORDER_COLOR,
        }
        self.main_links: dict[str, Any] = {}  # used to track the generated pages
        self.request_data = _map_privacy_request(privacy_request)
        self.dsr_data = dsr_data

    def _populate_template(
        self,
        template_path: str,
        heading: Optional[str] = None,
        description: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Populates the template with the given data.

        Args:
            template_path: the path to the template to populate
            heading: the heading to display on the template
            description: the description to display on the template
            data: the data to populate the template with

        Returns:
            The rendered template as a string.
        """
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
        """
        Adds a file to the zip file.

        Args:
            filename: the name of the file to add
            contents: the contents of the file to add
        """
        if filename and contents:
            self.out.writestr(f"{filename}", contents.encode("utf-8"))

    def _add_dataset(self, dataset_name: str, collections: dict[str, Any]) -> None:
        """
        Adds a dataset to the zip file.

        Args:
            dataset_name: the name of the dataset to add
            collections: the collections to add to the dataset
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

    def _write_attachment_content(
        self,
        file_name: str,
        content: Any,
        content_type: str,
        directory: str,
    ) -> None:
        """
        Writes attachment content to the specified directory, handling different content types appropriately.

        Args:
            file_name: The name of the file to write
            content: The content to write
            content_type: The content type of the file
            directory: The directory to write to (without trailing slash)
        """
        if not content:
            return

        # Handle text-based content types
        if content_type.startswith("text/"):
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            self._add_file(f"{directory}/{file_name}", content)
            return

        # Handle image content types
        if content_type.startswith("image/"):
            if not isinstance(content, bytes):
                content = content.encode("utf-8")
            self.out.writestr(f"{directory}/{file_name}", content)
            return

        # Handle document content types
        if content_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/zip",
        ]:
            if not isinstance(content, bytes):
                content = content.encode("utf-8")
            self.out.writestr(f"{directory}/{file_name}", content)
            return

        # For any other content type, treat as binary
        if not isinstance(content, bytes):
            content = content.encode("utf-8")
        self.out.writestr(f"{directory}/{file_name}", content)

    def _add_collection(
        self, rows: list[dict[str, Any]], dataset_name: str, collection_name: str
    ) -> None:
        """
        Adds a collection to the zip file.

        Args:
            rows: the rows to add to the collection
            dataset_name: the name of the dataset to add the collection to
            collection_name: the name of the collection to add
        """
        items_content = []

        for index, collection_item in enumerate(rows, 1):
            # Process any attachments in the item
            if "attachments" in collection_item and isinstance(
                collection_item["attachments"], list
            ):
                for attachment in collection_item["attachments"]:
                    file_name = attachment.get("file_name", "unknown")
                    content = attachment.get("content")
                    content_type = attachment.get("content_type", "")
                    self._write_attachment_content(
                        file_name,
                        content,
                        content_type,
                        f"data/{dataset_name}/{collection_name}",
                    )

            # Add item content to the list
            items_content.append(
                {
                    "index": index,
                    "heading": f"{collection_name} (item #{index})",
                    "data": collection_item,
                }
            )

        # Generate the collection index page
        self._add_file(
            f"data/{dataset_name}/{collection_name}/index.html",
            self._populate_template(
                "templates/collection_index.html",
                collection_name,
                None,
                {"collection_items": items_content},
            ),
        )

    def _add_attachments(self, attachments: list[dict[str, Any]]) -> None:
        """
        Adds top-level attachments to the zip file.

        Args:
            attachments: the attachments to add
        """
        if not attachments or not isinstance(attachments, list):
            return

        # Create attachment links for the index page
        attachment_links = {}
        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue

            file_name = attachment.get("file_name", "unknown")
            content = attachment.get("content")
            content_type = attachment.get("content_type", "")
            attachment_links[file_name] = f"{file_name}"

            # Write the attachment to the top-level attachments directory
            self._write_attachment_content(
                file_name, content, content_type, "attachments"
            )

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

    def _get_datasets_from_dsr_data(self) -> dict[str, Any]:
        """
        Returns the datasets from the DSR data.
        """
        # pre-process data to split the dataset:collection keys
        datasets: dict[str, Any] = defaultdict(lambda: defaultdict(list))
        for key, rows in self.dsr_data.items():

            # we handle attachments separately
            if key == "attachments":
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

        return datasets

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
            datasets = self._get_datasets_from_dsr_data()

            # Sort datasets alphabetically, excluding special cases
            regular_datasets = [
                name for name in sorted(datasets.keys()) if name != "dataset"
            ]  # pylint: disable=invalid-name

            # Add regular datasets in alphabetical order
            for dataset_name in regular_datasets:
                self._add_dataset(dataset_name, datasets[dataset_name])
                self.main_links[dataset_name] = f"data/{dataset_name}/index.html"

            # Add Additional Data if it exists
            if "dataset" in datasets:
                self._add_dataset("dataset", datasets["dataset"])
                self.main_links["Additional Data"] = "data/dataset/index.html"

            # Add Additional Attachments last if it exists
            if "attachments" in self.dsr_data:
                self._add_attachments(self.dsr_data["attachments"])
                self.main_links["Additional Attachments"] = "attachments/index.html"

            logger.info(f"Main links for welcome page: {self.main_links}")
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
        logger.info("DSR report generation complete.")
        return self.baos


def _map_privacy_request(privacy_request: PrivacyRequest) -> dict[str, Any]:
    """Creates a map with a subset of values from the privacy request"""
    request_data: dict[str, Any] = {}
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
