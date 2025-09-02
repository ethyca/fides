import json
import os
import time as time_module
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import jinja2
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from fides.api.schemas.policy import ActionType
from fides.api.service.storage.util import get_unique_filename
from fides.api.util.storage_util import StorageJSONEncoder, format_size

DSR_DIRECTORY = Path(__file__).parent.resolve()

TEXT_COLOR = "#4A5568"
HEADER_COLOR = "#FAFAFA"
BORDER_COLOR = "#E2E8F0"

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest  # pragma: no cover


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

    Args:
        privacy_request: the privacy request object
        dsr_data: the DSR data
    """

    def __init__(
        self,
        privacy_request: "PrivacyRequest",
        dsr_data: dict[str, Any],
        enable_streaming: bool = False,
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

        # to pass in custom colors in the future
        self.template_data: dict[str, Any] = {
            "text_color": TEXT_COLOR,
            "header_color": HEADER_COLOR,
            "border_color": BORDER_COLOR,
            "download_link_ttl_days": self._get_download_link_ttl_days(),
        }
        self.main_links: dict[str, Any] = {}  # used to track the generated pages

        # report data to populate the templates
        self.request_data = _map_privacy_request(privacy_request)
        self.dsr_data = dsr_data
        self.enable_streaming = enable_streaming

        # Track used filenames globally to match streaming storage behavior
        self.used_filenames: set[str] = set()

        # Track attachments by their unique identifier to prevent duplicate processing
        # Maps (download_url, file_name) -> unique_filename
        self.processed_attachments: dict[tuple[str, str], str] = {}

    def _get_download_link_ttl_days(self) -> int:
        """Get the download link TTL in days from the security configuration."""
        from fides.config import CONFIG

        return int(CONFIG.security.subject_request_download_link_ttl_seconds / 86400)

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
        Generates a page for each collection in the dataset and an index page for the dataset.
        Tracks the generated links to build a root level index after each collection has been processed.

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
        attachments: list[dict[str, Any]],
        directory: str,
        dataset_name: str = "attachments",
    ) -> dict[str, dict[str, str]]:
        """
        Processes attachments and returns a dictionary mapping filenames to their download URLs and sizes.

        Args:
            attachments: The attachments to process
            directory: The directory path (unused for presigned URLs)

        Returns:
            Dictionary mapping filenames to dictionaries containing url and size
        """
        # First process all attachments into a list of tuples (filename, data)
        processed_attachments = []

        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue

            file_name = attachment.get("file_name")
            if not file_name:
                logger.warning("Skipping attachment with no file name")
                continue

            download_url = attachment.get("download_url")
            if not download_url:
                logger.warning("Skipping attachment with no download URL")
                continue

            file_size = attachment.get("file_size")
            if isinstance(file_size, (int, float)):
                file_size = format_size(float(file_size))
            else:
                file_size = "Unknown"

            # Check if this attachment has already been processed
            attachment_key = (download_url, file_name)
            if attachment_key in self.processed_attachments:
                # Use the previously generated unique filename
                unique_filename = self.processed_attachments[attachment_key]
            else:
                # Get a unique filename to prevent duplicates globally
                unique_filename = get_unique_filename(file_name, self.used_filenames)
                self.used_filenames.add(unique_filename)
                # Track this attachment to prevent duplicate processing
                self.processed_attachments[attachment_key] = unique_filename

            # Use local attachment path when streaming is enabled
            if self.enable_streaming:
                # Calculate relative path from the current directory to attachments
                if directory.startswith("data/"):
                    # For collection data, go up to root then to attachments
                    depth = directory.count("/") + 1  # +1 for the attachments directory
                    relative_path = "../" * depth + f"attachments/{unique_filename}"
                else:
                    # For top-level attachments, just use the filename
                    relative_path = unique_filename
                attachment_url = relative_path
            else:
                attachment_url = download_url

            # Add to processed attachments
            processed_attachments.append(
                (
                    unique_filename,
                    {
                        "url": attachment_url,
                        "size": file_size,
                        "original_name": file_name,
                    },
                )
            )

        # Convert list of tuples to dictionary
        return dict(processed_attachments)

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
            # Create a copy of the item data to avoid modifying the original
            item_data = collection_item.copy()

            # Process any attachments in the item
            # First check for direct attachments key
            if "attachments" in item_data and isinstance(
                item_data["attachments"], list
            ):
                # Process attachments and get their URLs
                attachment_links = self._write_attachment_content(
                    item_data["attachments"],
                    f"data/{dataset_name}/{collection_name}",
                    dataset_name,
                )
                # Add the attachment URLs to the item data
                item_data["attachments"] = attachment_links
            else:
                # Check for nested attachment fields (ManualTask format)
                attachment_fields_found = []
                for field_name, field_value in item_data.items():
                    if isinstance(field_value, list) and field_value:
                        # Check if this field contains attachment-like data
                        first_item = field_value[0]
                        if isinstance(first_item, dict) and all(
                            key in first_item
                            for key in ["file_name", "download_url", "file_size"]
                        ):
                            attachment_fields_found.append(field_name)

                            # Process attachments and get their URLs
                            attachment_links = self._write_attachment_content(
                                field_value,
                                f"data/{dataset_name}/{collection_name}",
                                dataset_name,
                            )

                            # Replace the field value with processed attachment links
                            item_data[field_name] = attachment_links

            # Add item content to the list
            items_content.append(
                {
                    "index": index,
                    "heading": f"{collection_name} (item #{index})",
                    "data": item_data,
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

        # Process attachments and get the links
        attachment_links = self._write_attachment_content(attachments, "attachments")

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
        start_time = time_module.time()
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
            datasets: dict[str, Any] = self._get_datasets_from_dsr_data()

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
            # Only add attachments that weren't already processed in collections
            if "attachments" in self.dsr_data:
                # Filter out attachments that were already processed in collections
                unprocessed_attachments = []
                for attachment in self.dsr_data["attachments"]:
                    attachment_key = (
                        attachment.get("download_url"),
                        attachment.get("file_name"),
                    )
                    if attachment_key not in self.processed_attachments:
                        unprocessed_attachments.append(attachment)

                if unprocessed_attachments:
                    self._add_attachments(unprocessed_attachments)
                    self.main_links["Additional Attachments"] = "attachments/index.html"

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

        # Calculate time taken and file size
        time_taken = time_module.time() - start_time
        file_size = format_size(float(len(self.baos.getvalue())))

        logger.bind(time_to_generate=time_taken, dsr_package_size=file_size).info(
            "DSR report generation complete."
        )
        return self.baos


def _map_privacy_request(privacy_request: "PrivacyRequest") -> dict[str, Any]:
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
