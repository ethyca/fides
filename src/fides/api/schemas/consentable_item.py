from typing import List, Optional, Type

from pydantic import BaseModel, Field

from fides.api.models.consent_automation import ConsentableItem as ConsentableItemModel


class ConsentableItem(BaseModel):
    """
    Schema to represent 3rd-party consentable items and privacy notice relationships.
    """

    id: str
    type: str
    name: str
    notice_id: Optional[str] = None
    children: List["ConsentableItem"] = Field(default_factory=list)
    unmapped: Optional[bool] = False

    @classmethod
    def from_orm(
        cls: Type["ConsentableItem"], obj: ConsentableItemModel
    ) -> "ConsentableItem":
        item = cls(
            id=obj.external_id,
            type=obj.type,
            name=obj.name,
            notice_id=obj.notice_id,
        )
        # recursively set children
        item.children = [
            cls.from_orm(child) for child in getattr(obj, "children", [])  # type: ignore[pydantic-orm]
        ]
        return item


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

        if source.id == target.id:
            source.unmapped = False
            source.notice_id = target.notice_id
            target_children_map = {child.id: child for child in target.children}

            for child in source.children:
                target_child = target_children_map.get(child.id)
                if target_child is not None:
                    merge_consentable_items_recursive(child, target_child)

    # create a map of target items for efficient lookup
    db_item_map = {item.id: item for item in db_items}

    # iterate through API items and merge
    for api_item in api_items:
        target_item = db_item_map.get(api_item.id)
        merge_consentable_items_recursive(api_item, target_item)

    return api_items
