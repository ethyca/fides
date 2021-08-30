"""This module handles the logic required for applying manifest files to the server."""
from pprint import pprint
from typing import Dict, List, Tuple, Optional, Iterable

from deepdiff import DeepDiff

from fidesctl.cli.utils import handle_cli_response
from fidesctl.core import api
from fidesctl.core.utils import echo_green
from fideslang import FidesModel
from fideslang.manifests import ingest_manifests
from fideslang.models.validation import FidesKey
from fideslang.parse import (
    load_manifests_into_taxonomy,
    parse_manifest,
)


def sort_create_update_unchanged(
    manifest_object_list: List[FidesModel],
    server_object_list: List[FidesModel],
    diff: bool = False,
) -> Tuple[List[FidesModel], List[FidesModel], List[FidesModel]]:
    """
    Check the contents of the object lists and populate separate
    new lists for object creation, updating, or no change.

    The `diff` flag will print out the differences between the server objects
    the local resource files.
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
                if diff:
                    print(f"\nUpdated object with fidesKey: {manifest_object.fidesKey}")
                    pprint(DeepDiff(server_object, manifest_object))
                update_list.append(manifest_object)

        else:
            if diff:
                print(f"\nNew object with fidesKey: {manifest_object.fidesKey}")
                pprint(manifest_object)
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
            ),
            verbose=False,
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
            ),
            verbose=False,
        )
        echo_green(success_echo.format("Updated", object_type, update_object.fidesKey))
    for unchanged_object in unchanged_list:
        echo_green(
            success_echo.format("No changes to", object_type, unchanged_object.fidesKey)
        )


def get_server_objects(
    url: str, object_type: str, existing_keys: List[FidesKey], headers: Dict[str, str]
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
        parse_manifest(object_type, _object, from_server=True)
        for _object in raw_server_object_list
    ]
    return server_object_list


def echo_results(action: str, object_type: str, resource_list: List) -> None:
    """
    Echo out the results of the apply.
    """
    echo_green(f"{action.upper()} {len(resource_list)} {object_type} objects.")


def apply(
    url: str,
    manifests_dir: str,
    headers: Dict[str, str],
    dry: bool = False,
    diff: bool = False,
) -> None:
    """
    Apply the current manifest file state to the server.
    Excludes systems and registries.
    """
    ingested_manifests = ingest_manifests(manifests_dir)
    taxonomy = load_manifests_into_taxonomy(ingested_manifests)

    for object_type, resource_list in taxonomy.dict(
        by_alias=True, exclude_none=True
    ).items():
        # Doing some echos here to make a pretty output
        echo_green("-" * 10)

        resource_list = [
            parse_manifest(object_type, resource) for resource in resource_list
        ]
        existing_keys = [resource.fidesKey for resource in resource_list]
        server_object_list = get_server_objects(
            url, object_type, existing_keys, headers
        )

        # Determine which objects should be created, updated, or are unchanged
        create_list, update_list, unchanged_list = sort_create_update_unchanged(
            resource_list, server_object_list, diff
        )

        if dry:
            echo_results("would create", object_type, create_list)
            echo_results("would update", object_type, update_list)
            echo_results("would skip", object_type, unchanged_list)
        else:
            execute_create_update_unchanged(
                url,
                headers,
                object_type,
                create_list,
                update_list,
                unchanged_list,
            )

            echo_results("created", object_type, create_list)
            echo_results("updated", object_type, update_list)
            echo_results("skipped", object_type, unchanged_list)
    echo_green("-" * 10)
