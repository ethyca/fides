import logging
from typing import Any, Dict, List, Optional

from fidesops.ops.graph.config import FieldPath
from fidesops.ops.graph.traversal import TraversalNode
from fidesops.ops.models.connectionconfig import ConnectionTestStatus
from fidesops.ops.models.policy import CurrentStep, Policy, Rule
from fidesops.ops.models.privacy_request import ManualAction, PrivacyRequest
from fidesops.ops.service.connectors.base_connector import BaseConnector
from fidesops.ops.service.connectors.query_config import ManualQueryConfig
from fidesops.ops.util.collection_util import Row, append

logger = logging.getLogger(__name__)


class EmailConnector(BaseConnector[None]):
    def query_config(self, node: TraversalNode) -> ManualQueryConfig:
        """Intentionally reusing the ManualQueryConfig here. We're only using methods off of the base
        QueryConfig class here.
        """
        return ManualQueryConfig(node)

    def create_client(self) -> None:
        """Stub"""

    def close(self) -> None:
        """N/A for the EmailConnector"""

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Override to skip connection test for now
        """
        return ConnectionTestStatus.skipped

    def retrieve_data(  # type: ignore
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> Optional[List[Row]]:
        """Access requests are not supported at this time."""
        return []

    def mask_data(  # type: ignore
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
    ) -> Optional[int]:
        """Cache instructions for how to mask data in this collection.
        One email will be sent for all collections in this dataset at the end of the privacy request execution.
        """

        manual_action: ManualAction = self.build_masking_instructions(
            node, policy, input_data
        )

        logger.info("Caching action needed for collection: '%s", node.address.value)
        privacy_request.cache_email_connector_template_contents(
            step=CurrentStep.erasure,
            collection=node.address,
            action_needed=[manual_action],
        )

        return 0  # Fidesops itself does not mask this collection.

    def build_masking_instructions(
        self, node: TraversalNode, policy: Policy, input_data: Dict[str, List[Any]]
    ) -> ManualAction:
        """
        Generate information on how to find and mask relevant records on this collection.

        Because we don't have any rows from a completed "access request" for this source, we pass on both "access"
        and "erasure" instructions to the source.
        """

        # Values for locating relevant records on the current collection.
        locators: Dict[str, Any] = node.typed_filtered_values(input_data)
        # Add additional locators from the same dataset for which we don't have data
        for edge in node.incoming_edges_from_same_dataset():
            append(locators, edge.f2.field_path.string_path, str(edge.f1))

        # Build which fields to mask and how to mask
        fields_to_mask_by_rule: Dict[Rule, List[FieldPath]] = self.query_config(
            node
        ).build_rule_target_field_paths(policy)
        mask_map: Dict[str, Any] = {}
        for rule, field_paths in fields_to_mask_by_rule.items():
            for rule_field_path in field_paths:
                # Map field paths to the specified masking strategy.  If multiple rules target
                # the same field path, the last one will win
                mask_map[rule_field_path.string_path] = (
                    rule.masking_strategy.get("strategy")
                    if rule.masking_strategy
                    else None
                )

        # Returns a ManualAction even if there are no fields to mask on this collection,
        # because the locators still may be needed to find data to mask on dependent collections
        return ManualAction(locators=locators, update=mask_map if mask_map else None)
