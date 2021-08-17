"""This module handles the logic required for applying manifest files to the server."""
from typing import Dict, List, Tuple, Optional, Iterable

from fidesctl.core import api, manifests, parse
from fidesctl.core.models import FidesModel
from fidesctl.cli.utils import handle_cli_response
from .utils import echo_green


def sort_create_update_unchanged(
    manifest_object_list: List[FidesModel], server_object_list: List[FidesModel]
) -> Tuple[List[FidesModel], List[FidesModel], List[FidesModel]]:
    """
    Check the contents of the object lists and populate separate
    new lists for object creation, updating, or no change.
    """
    server_object_dict = {
        server_object.fidesKey: server_object for server_object in server_object_list
    }

    create_list = []
    update_list = []
    unchanged_list = []
    for manifest_object in manifest_object_list:
        object_key = manifest_object.fidesKey

        # Check if the object's fidesKey matches one from the server
        if object_key in server_object_dict.keys():
            server_object = server_object_dict[object_key]
            # Copy the ID since manifest files don't have them
            manifest_object.id = server_object.id

            if manifest_object == server_object:
                unchanged_list.append(manifest_object)
            else:
                update_list.append(manifest_object)

        else:
            create_list.append(manifest_object)

    return create_list, update_list, unchanged_list


def execute_create_update_unchanged(
    url: str,
    headers: Dict[str, str],
    object_type: str,
    create_list: Optional[List[FidesModel]] = None,
    update_list: Optional[List[FidesModel]] = None,
    unchanged_list: Optional[List[FidesModel]] = None,
) -> None:
    """
    Create, update, or just log objects based on which list they're in.
    """
    create_list = create_list or []
    update_list = update_list or []
    unchanged_list = unchanged_list or []
    success_echo = "{} {} with fidesKey: {}"

    for create_object in create_list:
        handle_cli_response(
            api.create(
                url=url,
                headers=headers,
                object_type=object_type,
                json_object=create_object.json(exclude_none=True),
            )
        )
        echo_green(success_echo.format("Created", object_type, create_object.fidesKey))
    for update_object in update_list:
        handle_cli_response(
            api.update(
                url=url,
                headers=headers,
                object_type=object_type,
                object_id=update_object.id,
                json_object=update_object.json(exclude_none=True),
            )
        )
        echo_green(success_echo.format("Updated", object_type, update_object.fidesKey))
    for unchanged_object in unchanged_list:
        echo_green(
            success_echo.format("No changes to", object_type, unchanged_object.fidesKey)
        )


def get_server_objects(
    url: str, object_type: str, existing_keys: List[str], headers: Dict[str, str]
) -> List[FidesModel]:
    """
    Get a list of objects from the server that match the provided keys.
    """
    raw_server_object_list: Iterable[Dict] = filter(
        None,
        [
            api.find(url, object_type, key, headers).json().get("data")
            for key in existing_keys
        ],
    )
    server_object_list: List[FidesModel] = [
        parse.parse_manifest(object_type, _object, from_server=True)
        for _object in raw_server_object_list
    ]
    return server_object_list


def apply(url: str, manifests_dir: str, headers: Dict[str, str]) -> None:
    """
    Apply the current manifest file state to the server.
    Excludes systems and registries.
    """
    ingested_manifests = manifests.ingest_manifests(manifests_dir)

    parsed_manifests: Dict[str, List[FidesModel]] = {
        object_type: [
            parse.parse_manifest(object_type, _object) for _object in object_list
        ]
        for object_type, object_list in ingested_manifests.items()
    }

    # Loop through each type of object and check for operations
    for object_type, manifest_object_list in parsed_manifests.items():

        existing_keys = [
            manifest_object.fidesKey for manifest_object in manifest_object_list
        ]
        server_object_list = get_server_objects(
            url, object_type, existing_keys, headers
        )

        # Determine which objects should be created, updated, or are unchanged
        create_list, update_list, unchanged_list = sort_create_update_unchanged(
            manifest_object_list,
            server_object_list,
        )
        execute_create_update_unchanged(
            url,
            headers,
            object_type,
            create_list,
            update_list,
            unchanged_list,
        )

        echo_green(f"Created {len(create_list)} {object_type} objects.")
        echo_green(f"Updated {len(update_list)} {object_type} objects.")
        echo_green(f"Skipped {len(unchanged_list)} unchanged {object_type} objects.")
