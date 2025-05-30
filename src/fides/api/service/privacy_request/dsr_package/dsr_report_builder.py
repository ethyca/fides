import json
import os
import time as time_module
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, Iterator, Optional

import jinja2
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.service.storage.util import AllowedFileType
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

        # to pass in custom colors in the future
        self.template_data: dict[str, Any] = {
            "text_color": TEXT_COLOR,
            "header_color": HEADER_COLOR,
            "border_color": BORDER_COLOR,
        }
        self.main_links: dict[str, Any] = {}  # used to track the generated pages

        # report data to populate the templates
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

    def _get_unique_filename(self, directory: str, filename: str) -> str:
        """
        Generates a unique filename by appending a counter if the file already exists.

        Args:
            directory: The directory path
            filename: The original filename

        Returns:
            A unique filename that won't conflict with existing files
        """
        base_name, extension = os.path.splitext(filename)
        counter = 1
        unique_filename = filename

        # Check if file exists in zip
        while f"{directory}/{unique_filename}" in self.out.namelist():
            unique_filename = f"{base_name}_{counter}{extension}"
            counter += 1

        return unique_filename

    def _write_attachment_content(
        self,
        file_name: str,
        content: Any,
        content_type: str,
        directory: str,
    ) -> None:
        """
        Writes attachment content to the specified directory, handling different content types appropriately.
        Uses streaming for large files to minimize memory usage.

        Args:
            file_name: The name of the file to write
            content: The content to write
            content_type: The content type of the file
            directory: The directory to write to (without trailing slash)
        """
        if not content:
            return

        # Get a unique filename to prevent duplicates
        unique_filename = self._get_unique_filename(directory, file_name)
        if unique_filename != file_name:
            logger.debug(
                "Renamed duplicate file from {} to {}", file_name, unique_filename
            )

        # Handle text-based content types
        if content_type in [AllowedFileType.txt.value, AllowedFileType.csv.value]:
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            self._add_file(f"{directory}/{unique_filename}", content)
            return

        # Handle binary content types
        if not isinstance(content, bytes):
            content = content.encode("utf-8")

        # For large files, write in chunks to minimize memory usage
        chunk_size = 1024 * 1024  # 1MB chunks
        if len(content) > chunk_size:
            with BytesIO(content) as content_stream:
                while chunk := content_stream.read(chunk_size):
                    self.out.writestr(
                        f"{directory}/{unique_filename}", chunk, zipfile.ZIP_DEFLATED
                    )
        else:
            self.out.writestr(f"{directory}/{unique_filename}", content)

    def _process_attachments_in_chunks(
        self, attachments: list[dict[str, Any]], chunk_size: int = 10
    ) -> Iterator[list[dict[str, Any]]]:
        """
        Process attachments in smaller chunks to reduce memory usage.

        Args:
            attachments: List of attachments to process
            chunk_size: Number of attachments to process at once

        Yields:
            Chunks of processed attachments
        """
        for i in range(0, len(attachments), chunk_size):
            chunk = attachments[i : i + chunk_size]
            processed_chunk = []
            for attachment in chunk:
                if not isinstance(attachment, dict):
                    continue

                file_name = attachment.get("file_name")
                if not file_name:  # Skip if no file name
                    logger.warning("Skipping attachment with no file name")
                    continue

                content = attachment.get("content")
                content_type = attachment.get("content_type", "")

                if content:
                    processed_chunk.append(
                        {
                            "file_name": file_name,
                            "content": content,
                            "content_type": content_type,
                        }
                    )
                else:
                    logger.warning("Skipping attachment with no content")
            yield processed_chunk

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
            item_attachment_links = {}  # Track unique filenames for this specific item

            # Process any attachments in the item
            if "attachments" in collection_item and isinstance(
                collection_item["attachments"], list
            ):
                # Process attachments in chunks to minimize memory usage
                for chunk in self._process_attachments_in_chunks(
                    collection_item["attachments"]
                ):
                    for attachment in chunk:
                        directory = f"data/{dataset_name}/{collection_name}"
                        unique_filename = self._get_unique_filename(
                            directory, attachment["file_name"]
                        )
                        item_attachment_links[unique_filename] = unique_filename
                        self._write_attachment_content(
                            unique_filename,
                            attachment["content"],
                            attachment["content_type"],
                            directory,
                        )

            # Add item content to the list
            items_content.append(
                {
                    "index": index,
                    "heading": f"{collection_name} (item #{index})",
                    "data": collection_item,
                    "attachments": item_attachment_links,  # Use item-specific attachment links
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
        Processes attachments in chunks to minimize memory usage.

        Args:
            attachments: the attachments to add
        """
        if not attachments or not isinstance(attachments, list):
            return

        # Create attachment links for the index page
        attachment_links = {}

        # Process attachments in chunks
        for chunk in self._process_attachments_in_chunks(attachments):
            for attachment in chunk:
                file_name = attachment["file_name"]
                content = attachment["content"]
                content_type = attachment["content_type"]

                # Get unique filename for the attachment
                unique_filename = self._get_unique_filename("attachments", file_name)

                # Store the unique filename in the links dictionary
                attachment_links[unique_filename] = unique_filename

                # Write the attachment to the top-level attachments directory
                self._write_attachment_content(
                    unique_filename, content, content_type, "attachments"
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

    def _format_size(self, size_bytes: float) -> str:
        """
        Format size in bytes to human readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string with appropriate unit (B, KB, MB, GB)
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

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
            if "attachments" in self.dsr_data:
                self._add_attachments(self.dsr_data["attachments"])
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
        file_size = self._format_size(float(len(self.baos.getvalue())))

        logger.bind(time_to_generate=time_taken, dsr_package_size=file_size).info(
            "DSR report generation complete."
        )
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
