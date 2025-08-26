import json
import os
import re
import time as time_module
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, List, Optional

import jinja2
from fideslang.models import Dataset, DatasetField
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from sqlalchemy.orm import Session, object_session

from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request_redaction_patterns import (
    PrivacyRequestRedactionPatterns,
)
from fides.api.schemas.policy import ActionType
from fides.api.util.storage_util import StorageJSONEncoder, format_size

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

        # Track used filenames across all attachments
        self.used_filenames: set[str] = set()

        self.redaction_patterns: List[str] = []

        # Set of entity names that should be redacted
        self.entities_to_redact = set()

        # Load redaction patterns and entities to redact from database
        db = object_session(privacy_request)
        if db is not None:
            # Load redaction patterns from database using the privacy request's session
            if patterns := PrivacyRequestRedactionPatterns.get_patterns(db):
                self.redaction_patterns = patterns
            self.entities_to_redact = get_redaction_entities_map(db)

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

    def _add_dataset(
        self, dataset_name: str, collections: dict[str, Any], index: int
    ) -> None:
        """
        Generates a page for each collection in the dataset and an index page for the dataset.
        Tracks the generated links to build a root level index after each collection has been processed.

        Args:
            dataset_name: the name of the dataset to add
            collections: the collections to add to the dataset
            index: index of the dataset
        """
        # compute final dataset name once (may be redacted)
        dataset_display_name = self._redact_name("dataset", dataset_name, index)

        # track links to collection indexes
        collection_links = {}
        for collection_index, (original_collection_name, rows) in enumerate(
            collections.items(), start=1
        ):
            collection_display_name = self._redact_name(
                "collection", original_collection_name, collection_index, dataset_name
            )
            collection_url = f"{collection_display_name}/index.html"
            self._add_collection(
                rows,
                dataset_display_name,
                collection_display_name,
                dataset_name,
                original_collection_name,
            )
            collection_links[collection_display_name] = collection_url

        # generate dataset index page
        self._add_file(
            f"data/{dataset_display_name}/index.html",
            self._populate_template(
                "templates/dataset_index.html",
                dataset_display_name,
                None,
                collection_links,
            ),
        )

    def _get_unique_filename(self, filename: str) -> str:
        """
        Generates a unique filename by appending a counter if the file already exists.
        Now tracks filenames across all directories to ensure global uniqueness.

        Args:
            filename: The original filename

        Returns:
            A unique filename that won't conflict with existing files
        """
        base_name, extension = os.path.splitext(filename)
        counter = 1
        unique_filename = filename

        # Check if file exists in used_filenames set
        while unique_filename in self.used_filenames:
            unique_filename = f"{base_name}_{counter}{extension}"
            counter += 1

        # Add the new filename to the set
        self.used_filenames.add(unique_filename)
        return unique_filename

    def _write_attachment_content(
        self,
        attachments: list[dict[str, Any]],
        directory: str,
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

            # Get a unique filename to prevent duplicates
            unique_filename = self._get_unique_filename(file_name)

            # Add to processed attachments
            processed_attachments.append(
                (unique_filename, {"url": download_url, "size": file_size})
            )

        # Convert list of tuples to dictionary
        return dict(processed_attachments)

    def _add_collection(
        self,
        rows: list[dict[str, Any]],
        dataset_display_name: str,
        collection_display_name: str,
        dataset_name: str,
        collection_name: str,
    ) -> None:
        """
        Adds a collection to the zip file.

        Args:
            rows: the rows to add to the collection
            dataset_display_name: the final dataset name to use for file paths
            collection_display_name: the final collection name to use for file paths
        """
        items_content = []

        for item_index, collection_item in enumerate(rows, 1):
            # Create a copy of the item data to avoid modifying the original
            item_data = collection_item.copy()

            # Process any attachments in the item
            if "attachments" in item_data and isinstance(
                item_data["attachments"], list
            ):
                # Process attachments and get their URLs
                attachment_links = self._write_attachment_content(
                    item_data["attachments"],
                    f"data/{dataset_display_name}/{collection_display_name}",
                )
                # Add the attachment URLs to the item data
                item_data["attachments"] = attachment_links

            # Add indexing to field names
            item_data_with_display_names = {}
            for field_index, (field_name, field_value) in enumerate(
                item_data.items(), start=1
            ):
                field_display_name = self._redact_name(
                    "field", field_name, field_index, dataset_name, collection_name
                )
                item_data_with_display_names[field_display_name] = field_value

            # Add item content to the list with item heading
            item_heading = f"{collection_display_name} (item #{item_index})"
            items_content.append(
                {
                    "index": item_index,
                    "heading": item_heading,
                    "data": item_data_with_display_names,
                }
            )

        # Generate the collection index page
        self._add_file(
            f"data/{dataset_display_name}/{collection_display_name}/index.html",
            self._populate_template(
                "templates/collection_index.html",
                collection_display_name,
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

    def _redact_name(
        self,
        name_type: str,
        name: str,
        index: int,
        dataset_name: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> str:
        """
        Helper function to create indexed names for datasets, collections, and fields.
        Applies redaction if the name matches any of the configured regex patterns OR
        if there's a fides_meta.redact: name configuration for this entity.

        Args:
            name_type: The type of name ("dataset", "collection", or "field")
            name: The original name to be indexed
            index: The index to use directly (should already be 1-based)
            dataset_name: The dataset name (for context in hierarchical keys)
            collection_name: The collection name (for context in hierarchical keys)

        Returns:
            Indexed name in the format "type_N" (e.g., "dataset_1", "collection_2", "field_3")
            if the name should be redacted, otherwise returns the original name.
        """
        # First check for fides_meta.redact: name configurations using hierarchical keys
        hierarchical_key = self._build_hierarchical_key(
            name_type, name, dataset_name, collection_name
        )
        if hierarchical_key in self.entities_to_redact:
            return f"{name_type}_{index}"

        # Fall back to global regex pattern matching
        if self.redaction_patterns:
            for pattern in self.redaction_patterns:
                try:
                    if re.search(pattern, name, re.IGNORECASE):
                        return f"{name_type}_{index}"
                except re.error:
                    # Skip invalid regex patterns
                    logger.warning(f"Invalid regex pattern: {pattern}")
                    continue

        # Return original name if no patterns match or no configurations found
        return name

    def _build_hierarchical_key(
        self,
        name_type: str,
        name: str,
        dataset_name: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> str:
        """
        Build hierarchical key for entity lookup.

        Args:
            name_type: The type of name ("dataset", "collection", or "field")
            name: The original name
            dataset_name: The dataset name
            collection_name: The collection name

        Returns:
            Hierarchical key for entity lookup
        """
        if name_type == "dataset":
            return name
        if name_type == "collection" and dataset_name:
            return f"{dataset_name}.{name}"
        if name_type == "field" and dataset_name and collection_name:
            return f"{dataset_name}.{collection_name}.{name}"
        return name

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
            for index, original_dataset_name in enumerate(regular_datasets, start=1):
                dataset_display_name = self._redact_name(
                    "dataset", original_dataset_name, index
                )
                self._add_dataset(
                    original_dataset_name, datasets[original_dataset_name], index
                )
                self.main_links[dataset_display_name] = (
                    f"data/{dataset_display_name}/index.html"
                )

            # Add Additional Data if it exists
            if "dataset" in datasets:
                additional_data_index = (
                    len(regular_datasets) + 1
                )  # Index after all regular datasets
                dataset_display_name = self._redact_name(
                    "dataset", "dataset", additional_data_index
                )
                self._add_dataset("dataset", datasets["dataset"], additional_data_index)
                self.main_links["Additional Data"] = (
                    f"data/{dataset_display_name}/index.html"
                )

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
        file_size = format_size(float(len(self.baos.getvalue())))

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


def _traverse_fields_for_redaction(
    fields: List[DatasetField], current_path: str, redaction_entities: set[str]
) -> None:
    """
    Recursively traverse nested fields to find redaction entities.

    Args:
        fields: List of field dictionaries to traverse
        current_path: Current hierarchical path (e.g., "dataset.collection")
        redaction_entities: Set to add redacted field paths to
    """
    for field in fields:
        field_name = field.name
        if not field_name:
            continue

        field_path = f"{current_path}.{field_name}"
        field_fides_meta = field.fides_meta

        if field_fides_meta and field_fides_meta.redact == "name":
            redaction_entities.add(field_path)

        # Recursively check nested fields
        if field.fields:
            _traverse_fields_for_redaction(field.fields, field_path, redaction_entities)


def get_redaction_entities_map(db: Session) -> set[str]:
    """
    Create a set of hierarchical entity keys that should be redacted based on fides_meta.redact: name.

    This utility function reads all enabled dataset configurations from the database
    and builds a set of hierarchical entity keys (dataset_name, dataset_name.collection_name,
    dataset_name.collection_name.field_name) that have fides_meta.redact set to "name".

    Supports deeply nested field structures with unlimited nesting depth.

    Args:
        db: Database session

    Returns:
        Set of hierarchical entity keys that should be redacted
    """
    redaction_entities = set()

    try:
        dataset_configs = DatasetConfig.all(db=db)

        for dataset_config in dataset_configs:
            ctl_dataset = dataset_config.ctl_dataset
            if not ctl_dataset:
                continue

            dataset = Dataset.model_validate(dataset_config.ctl_dataset)
            # Intentionally using the fides_key instead of name since it's always provided
            dataset_name = dataset.fides_key

            # Check dataset level
            if dataset.fides_meta and dataset.fides_meta.redact == "name":
                redaction_entities.add(dataset_name)

            # Check collection level
            for collection_dict in dataset.collections:
                # Collections are stored as dictionaries in the database
                collection_name = collection_dict.name
                if not collection_name:
                    continue

                collection_path = f"{dataset_name}.{collection_name}"
                collection_fides_meta = collection_dict.fides_meta

                if collection_fides_meta and collection_fides_meta.redact == "name":
                    redaction_entities.add(collection_path)

                # Check field level (with recursive nested field support)
                _traverse_fields_for_redaction(
                    collection_dict.fields, collection_path, redaction_entities
                )

    except Exception as exc:
        # Log error but don't fail, just return empty set
        logger.warning(f"Error extracting redaction configurations: {exc}")

    return redaction_entities


def get_redaction_entities_map_db(db: Session) -> set[str]:
    """
    Create a set of hierarchical entity keys that should be redacted based on fides_meta.redact: name.

    This function uses PostgreSQL's JSON processing capabilities directly in the database
    for better performance. It extracts datasets, collections, and fields (including nested fields)
    that have fides_meta->>'redact' = 'name'.

    Args:
        db: Database session

    Returns:
        Set of hierarchical entity keys that should be redacted
    """
    redaction_entities = set()

    try:
        # Query for dataset-level redactions
        dataset_query = """
        SELECT ctl.fides_key as entity_path
        FROM datasetconfig dc
        JOIN ctl_datasets ctl ON dc.ctl_dataset_id = ctl.id
        WHERE ctl.fides_meta->>'redact' = 'name'
        """

        dataset_results = db.execute(dataset_query).fetchall()
        for row in dataset_results:
            redaction_entities.add(row[0])

        # Query for collection-level redactions
        collection_query = """
        SELECT ctl.name || '.' || (collection_elem->>'name') as entity_path
        FROM datasetconfig dc
        JOIN ctl_datasets ctl ON dc.ctl_dataset_id = ctl.id
        CROSS JOIN LATERAL jsonb_array_elements(ctl.collections::jsonb) AS collection_elem
        WHERE collection_elem->'fides_meta'->>'redact' = 'name'
            AND collection_elem->>'name' IS NOT NULL
        """

        collection_results = db.execute(collection_query).fetchall()
        for row in collection_results:
            redaction_entities.add(row[0])

        # Query for field-level redactions (including nested fields)
        # This uses a recursive CTE to handle arbitrary nesting levels
        field_query = """
        WITH RECURSIVE field_hierarchy AS (
            -- Base case: top-level fields in collections
            SELECT
                ctl.name as dataset_name,
                collection_elem->>'name' as collection_name,
                field_elem->>'name' as field_name,
                ctl.name || '.' ||
                    (collection_elem->>'name') || '.' ||
                    (field_elem->>'name') as entity_path,
                field_elem->'fields' as nested_fields,
                field_elem->'fides_meta'->>'redact' as redact_value
            FROM datasetconfig dc
            JOIN ctl_datasets ctl ON dc.ctl_dataset_id = ctl.id
            CROSS JOIN LATERAL jsonb_array_elements(ctl.collections::jsonb) AS collection_elem
            CROSS JOIN LATERAL jsonb_array_elements(collection_elem->'fields') AS field_elem
            WHERE collection_elem->>'name' IS NOT NULL
                AND field_elem->>'name' IS NOT NULL

            UNION ALL

            -- Recursive case: nested fields
            SELECT
                fh.dataset_name,
                fh.collection_name,
                nested_field->>'name' as field_name,
                fh.entity_path || '.' || (nested_field->>'name') as entity_path,
                nested_field->'fields' as nested_fields,
                nested_field->'fides_meta'->>'redact' as redact_value
            FROM field_hierarchy fh
            CROSS JOIN LATERAL jsonb_array_elements(fh.nested_fields) AS nested_field
            WHERE fh.nested_fields IS NOT NULL
                AND jsonb_typeof(fh.nested_fields) = 'array'
                AND nested_field->>'name' IS NOT NULL
        )
        SELECT DISTINCT entity_path
        FROM field_hierarchy
        WHERE redact_value = 'name'
        """

        field_results = db.execute(field_query).fetchall()
        for row in field_results:
            redaction_entities.add(row[0])

    except Exception as exc:
        # Log error but don't fail, just return empty set
        logger.warning(
            f"Error extracting redaction configurations from database: {exc}"
        )

    return redaction_entities
