import copy
import json
import os
import time as time_module
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import jinja2
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from sqlalchemy.orm import object_session

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.privacy_request.dsr_package.dsr_data_preprocessor import (
    DSRDataPreprocessor,
)
from fides.api.service.privacy_request.dsr_package.utils import map_privacy_request
from fides.api.service.storage.util import (
    _get_datasets_from_dsr_data,
    create_attachment_info_dict,
    format_attachment_size,
    generate_attachment_url_from_storage_path,
    is_attachment_field,
    process_attachment_naming,
    process_attachments_contextually,
    resolve_path_from_context,
)
from fides.api.util.storage_util import StorageJSONEncoder, format_size
from fides.config import CONFIG

DSR_DIRECTORY = Path(__file__).parent.resolve()

TEXT_COLOR = "#4A5568"
HEADER_COLOR = "#FAFAFA"
BORDER_COLOR = "#E2E8F0"


# pylint: disable=too-many-instance-attributes
class DSRReportBuilder:
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
            "enable_streaming": enable_streaming,
        }
        self.main_links: dict[str, Any] = {}  # used to track the generated pages

        # Process the DSR data for redaction
        db = object_session(privacy_request)
        if db is not None:
            processor = DSRDataPreprocessor(db)
            processed_dsr_data = processor.process_dsr_data(dsr_data)
        else:
            # Fallback if no database session available
            processed_dsr_data = dsr_data

        # report data to populate the templates
        self.request_data = map_privacy_request(privacy_request)
        self.dsr_data = processed_dsr_data
        self.enable_streaming = enable_streaming

        # Track used filenames per dataset to prevent conflicts within the same dataset
        # Maps dataset_name -> set of used filenames
        self.used_filenames_per_dataset: dict[str, set[str]] = {}

        # Track attachments by their unique identifier to prevent duplicate processing
        # Maps (download_url, file_name) -> unique_filename
        self.processed_attachments: dict[tuple[str, str], str] = {}
        # Track which attachments were processed as dataset attachments (not top-level)
        self.dataset_processed_attachments: set[tuple[str, str]] = set()

    def _get_download_link_ttl_days(self) -> int:
        """Get the download link TTL in days from the security configuration."""
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

    # pylint: disable=too-many-branches
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

            # Get or create the used_filenames set for this dataset
            if dataset_name not in self.used_filenames_per_dataset:
                self.used_filenames_per_dataset[dataset_name] = set()
            used_filenames = self.used_filenames_per_dataset[dataset_name]

            # Process attachment naming using shared utility
            result = process_attachment_naming(
                attachment, used_filenames, self.processed_attachments, dataset_name
            )

            if result is None:  # Skip if processing failed
                continue

            unique_filename, attachment_key = result
            # Track that this attachment was processed as a dataset attachment
            self.dataset_processed_attachments.add(attachment_key)

            # Format file size using shared utility
            file_size = format_attachment_size(attachment.get("file_size"))

            # Determine the actual directory for this attachment based on its context
            actual_directory = resolve_path_from_context(attachment, directory)

            # Generate attachment URL using shared utility with actual storage path
            download_url = attachment.get("download_url")
            if not download_url:
                continue

            attachment_url = generate_attachment_url_from_storage_path(
                download_url,
                unique_filename,
                actual_directory,  # This is the base_path where the file will be stored
                actual_directory,  # This is the HTML template directory
                self.enable_streaming,
            )

            # Create attachment info dictionary using shared utility
            file_name = attachment.get("file_name")
            if not file_name:
                continue

            attachment_info = create_attachment_info_dict(
                attachment_url, file_size, file_name
            )

            processed_attachments.append((unique_filename, attachment_info))

        # Convert list of tuples to dictionary
        return dict(processed_attachments)

    def _get_processed_attachments_list(
        self, data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Get all processed attachments using shared contextual logic.

        Args:
            data: The DSR data dictionary

        Returns:
            List of processed attachment dictionaries
        """
        # Create temporary sets for compatibility with the shared function
        used_filenames_data = set()
        used_filenames_attachments = set()

        # Populate the temporary sets from our per-dataset tracking
        for dataset_name, filenames in self.used_filenames_per_dataset.items():
            if dataset_name == "attachments":
                used_filenames_attachments.update(filenames)
            else:
                used_filenames_data.update(filenames)

        processed_attachments_list = process_attachments_contextually(
            data,
            used_filenames_data,
            used_filenames_attachments,
            self.processed_attachments,
            enable_streaming=self.enable_streaming,
        )

        # Trust the contextual processing completely - it already correctly determines
        # context based on the attachment's location in the DSR data structure
        filtered_list = processed_attachments_list

        return filtered_list

    def _generate_attachment_url_from_index(
        self, context: dict[str, Any], unique_filename: str
    ) -> str:
        """Generate the correct URL from attachments/index.html to an attachment file.

        Args:
            context: The attachment context information
            unique_filename: The unique filename of the attachment

        Returns:
            The relative URL from attachments/index.html to the attachment file
        """
        # URL-encode the filename for proper HTML link functionality when streaming is enabled
        if self.enable_streaming:
            # Always encode the filename when streaming is enabled to ensure consistency
            encoded_filename = quote(unique_filename, safe="")
        else:
            encoded_filename = unique_filename

        if context.get("type") == "top_level":
            # Top-level attachments are in the same directory as the index
            return encoded_filename
        if context.get("type") in ["direct", "nested"]:
            # Dataset attachments are in data/dataset/collection/attachments/
            # From attachments/index.html, we need to go to ../data/dataset/collection/attachments/filename
            dataset = context.get("dataset", "unknown")
            collection = context.get("collection", "unknown")
            return f"../data/{dataset}/{collection}/attachments/{encoded_filename}"
        # Fallback for other cases - return just the filename (encoded if streaming)
        return encoded_filename

    def _create_attachment_info_with_corrected_url(
        self, attachment_info: dict[str, str], correct_url: str
    ) -> dict[str, str]:
        """Create attachment info with corrected URL.

        Args:
            attachment_info: The original attachment info
            correct_url: The corrected URL

        Returns:
            New attachment info with corrected URL and safe_url
        """
        corrected_attachment_info = attachment_info.copy()
        corrected_attachment_info["url"] = correct_url
        corrected_attachment_info["safe_url"] = correct_url
        return corrected_attachment_info

    def _add_collection(
        self,
        rows: list[dict[str, Any]],
        dataset_name: str,
        collection_name: str,
    ) -> None:
        """
        Adds a collection to the zip file.
        """
        items_content = []

        for item_index, collection_item in enumerate(rows, 1):
            # Create a deep copy of the item data to avoid modifying the original DSR data
            # This ensures the comprehensive attachments index can access unmodified attachments
            item_data = copy.deepcopy(collection_item)

            # Process any attachments in the item - First check for direct attachments key
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

            # Add item content to the list with item heading
            # Field names are already redacted in the processed data
            item_heading = f"{collection_name} (item #{item_index})"
            items_content.append(
                {
                    "index": item_index,
                    "heading": item_heading,
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

    def _add_comprehensive_attachments_index(self) -> None:
        """
        Creates a comprehensive attachments index that includes ALL attachments
        from all datasets and top-level attachments, with links pointing to their
        actual storage locations.
        """
        # Get all processed attachments using shared logic on original DSR data
        processed_attachments_list = self._get_processed_attachments_list(self.dsr_data)

        # Create a comprehensive attachment links dictionary with deduplication
        all_attachment_links = {}
        seen_attachment_keys = set()

        for processed_attachment in processed_attachments_list:
            unique_filename = processed_attachment["unique_filename"]
            attachment_info = processed_attachment["attachment_info"]
            context = processed_attachment["context"]
            attachment = processed_attachment["attachment"]

            # Create a unique key based on download_url to avoid duplicates
            attachment_key = attachment.get("download_url")
            if attachment_key in seen_attachment_keys:
                continue
            seen_attachment_keys.add(attachment_key)

            # Generate the correct URL based on streaming settings
            if self.enable_streaming:
                # For streaming mode, use local attachment references
                correct_url = self._generate_attachment_url_from_index(
                    context, unique_filename
                )
            else:
                # For non-streaming mode, use original download URLs
                correct_url = attachment.get("download_url", unique_filename)

            # Create a descriptive key that includes the source location
            if context.get("type") == "top_level":
                key = f"Top-level: {unique_filename}"
            elif context.get("type") in ["direct", "nested"]:
                dataset = context.get("dataset", "unknown")
                collection = context.get("collection", "unknown")
                key = f"{dataset}/{collection}: {unique_filename}"
            else:
                key = unique_filename

            # Create new attachment info with the correct URL
            corrected_attachment_info = self._create_attachment_info_with_corrected_url(
                attachment_info, correct_url
            )
            all_attachment_links[key] = corrected_attachment_info

        # Generate comprehensive attachments index page
        self._add_file(
            "attachments/index.html",
            self._populate_template(
                "templates/attachments_index.html",
                "All Attachments",
                "All files attached to this privacy request",
                all_attachment_links,
            ),
        )

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
            datasets: dict[str, Any] = _get_datasets_from_dsr_data(self.dsr_data)

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
                # Use a more friendly name for the link but keep the dataset name for the path
                self.main_links["Additional Data"] = "data/dataset/index.html"

            # Add comprehensive attachments index that includes ALL attachments
            # Check if there are any attachments at all (top-level or in datasets)
            has_top_level_attachments = (
                "attachments" in self.dsr_data and self.dsr_data["attachments"]
            )
            has_dataset_attachments = any(
                any(
                    "attachments" in item
                    or any(
                        is_attachment_field(field_value)
                        for field_value in item.values()
                        if isinstance(field_value, list)
                    )
                    for item in collection_items
                    if isinstance(item, dict)
                )
                for collection in datasets.values()
                if isinstance(collection, dict)
                for collection_items in collection.values()
                if isinstance(collection_items, list)
            )
            has_attachments = has_top_level_attachments or has_dataset_attachments

            if has_attachments:
                self._add_comprehensive_attachments_index()
                self.main_links["All Attachments"] = "attachments/index.html"

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
