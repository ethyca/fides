# pylint: disable=too-many-lines
from typing import Any, Dict, List, Optional, TypeVar

from sqlalchemy.sql import Executable  # type: ignore

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import ManualAction
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row, filter_nonempty_values

T = TypeVar("T")


class ManualQueryConfig(QueryConfig[Executable]):
    def generate_query(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy]
    ) -> Optional[ManualAction]:
        """Describe the details needed to manually retrieve data from the
        current collection.

        Example:
        {
            "step": "access",
            "collection": "manual_dataset:manual_collection",
            "action_needed": [
                {
                    "locators": {'email': "customer-1@example.com"},
                    "get": ["id", "box_id"]
                    "update":  {}
                }
            ]
        }

        """

        locators: Dict[str, Any] = self.node.typed_filtered_values(input_data)
        get: List[str] = [
            field_path.string_path
            for field_path in self.node.collection.top_level_field_dict
        ]

        if get and locators:
            return ManualAction(locators=locators, get=get, update=None)
        return None

    def query_to_str(self, t: T, input_data: Dict[str, List[Any]]) -> None:
        """Not used for ManualQueryConfig, we output the dry run query as a dictionary instead of a string"""

    def dry_run_query(self) -> Optional[ManualAction]:  # type: ignore
        """Displays the ManualAction needed with question marks instead of action data for the locators
        as a dry run query"""
        fake_data: Dict[str, Any] = self.display_query_data()
        manual_query: Optional[ManualAction] = self.generate_query(fake_data, None)
        if not manual_query:
            return None

        for where_params in manual_query.locators.values():
            for i, _ in enumerate(where_params):
                where_params[i] = "?"
        return manual_query

    def generate_update_stmt(
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> Optional[ManualAction]:
        """Describe the details needed to manually mask data in the
        current collection.

        Example:
         {
            "step": "erasure",
            "collection": "manual_dataset:manual_collection",
            "action_needed": [
                {
                    "locators": {'id': 1},
                    "get": []
                    "update":  {'authorized_user': None}
                }
            ]
        }
        """
        locators: Dict[str, Any] = filter_nonempty_values(
            {
                field_path.string_path: field.cast(row[field_path.string_path])
                for field_path, field in self.primary_key_field_paths.items()
            }
        )
        update_stmt: Dict[str, Any] = self.update_value_map(row, policy, request)

        if update_stmt and locators:
            return ManualAction(locators=locators, get=None, update=update_stmt)
        return None
