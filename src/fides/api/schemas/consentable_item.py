from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from fides.api.models.consent_automation import ConsentableItem as ConsentableItemModel
from fides.api.schemas.base_class import FidesSchema


class ConsentableItem(FidesSchema):
    """
    Schema to represent 3rd-party consentable items and privacy notice relationships.
    """

    external_id: str
    type: str
    name: str
    notice_id: Optional[str] = None
    children: List["ConsentableItem"] = Field(default_factory=list)
    unmapped: Optional[bool] = False


def merge_consentable_items(
    api_items: List[ConsentableItem], db_items: Optional[List[ConsentableItem]] = None
) -> List[ConsentableItem]:
    """
    Recursively merges the lists of consentable items, setting the unmapped flag if the item is not in the database.

    WARNING: This is a destructive operation for the api_items parameter.
    """

    if db_items is None:
        db_items = []

    def merge_consentable_items_recursive(
        source: ConsentableItem, target: Optional[ConsentableItem]
    ) -> None:
        if target is None:
            source.unmapped = True
            for child in source.children:
                child.unmapped = True
            return

        if source.external_id == target.external_id:
            source.unmapped = False
            source.notice_id = target.notice_id
            target_children_map = {
                child.external_id: child for child in target.children
            }

            for child in source.children:
                target_child = target_children_map.get(child.external_id)
                if target_child is not None:
                    merge_consentable_items_recursive(child, target_child)

    # create a map of target items for efficient lookup
    db_item_map = {item.external_id: item for item in db_items}

    # iterate through API items and merge
    for api_item in api_items:
        target_item = db_item_map.get(api_item.external_id)
        merge_consentable_items_recursive(api_item, target_item)

    return api_items


def build_consent_item_hierarchy(
    consentable_items: List[ConsentableItemModel],
) -> List[ConsentableItem]:
    """
    Builds a hierarchy of ConsentableItem Pydantic models from the flat list of database models.
    """

    return [
        ConsentableItem.model_validate(item)
        for item in consentable_items
        if item.parent_id is None
    ]


class ConsentWebhookResult(BaseModel):
    """
    A wrapper class for the identity map and notice map values returned from a `PROCESS_CONSENT_WEBHOOK` function.
    """

    identity_map: Dict[
        Literal["email", "phone_number", "fides_user_device", "external_id"], str
    ] = Field(default_factory=dict, description="The identity of the user.")
    notice_id_map: Dict[str, str] = Field(
        default_factory=dict,
        description="A map of privacy notice IDs to user consent preferences.",
    )
