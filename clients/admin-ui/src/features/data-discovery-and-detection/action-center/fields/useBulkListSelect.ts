import _ from "lodash";
import { useState } from "react";

type SelectMode = "inclusive" | "exclusive";

interface ListItem {
  itemKey: React.Key;
}

export const extractListItemKeys = <T extends ListItem>(data: Array<T>) =>
  data.map(({ itemKey }) => itemKey);

export const useBulkListSelect = <T extends ListItem>() => {
  const [mode, setMode] = useState<SelectMode>("inclusive");
  /** list of items currently in view */
  const [listItems, setListItemsState] = useState<Array<T>>([]);
  /**
   * Delta between selected vs non-selected elements
   * includes selected elements when in inclusive mode
   * will be deselected elements when in exclusive mode
   */
  const [delta, setDeltaState] = useState<Array<T>>([]);

  const setDelta = (newDelta: Array<T>) => {
    setDeltaState(_.uniqBy(newDelta, "itemKey"));
  };

  const updateSelectedListItem = (itemKey: React.Key, isSelected: boolean) => {
    const updatedItem = listItems.find((item) => itemKey === item.itemKey);

    if (updatedItem) {
      const updateMode: "add" | "remove" = (
        mode === "inclusive" ? isSelected : !isSelected
      )
        ? "add"
        : "remove";

      switch (updateMode) {
        case "add":
          setDelta([...delta, updatedItem]);
          break;
        default:
          setDelta(delta.filter((item) => item.itemKey !== itemKey));
      }
    }
  };

  const updateListSelectMode = (newMode: SelectMode) => {
    setMode(newMode);
    setDeltaState([]);
  };

  const resetListSelect = () => {
    setDeltaState([]);
    setMode("inclusive");
  };

  const inverseDelta = listItems.filter(
    ({ itemKey }) => !delta.find((d) => d.itemKey === itemKey),
  );
  const selectedListItems = mode === "inclusive" ? delta : inverseDelta;
  const excludedListItems = mode === "exclusive" ? delta : inverseDelta;

  return {
    excludedListItems,
    indeterminate:
      mode === "inclusive"
        ? selectedListItems.length > 0 &&
          listItems.length !== selectedListItems.length
        : excludedListItems.length > 0,
    isBulkSelect:
      mode === "inclusive"
        ? selectedListItems.length > 0 &&
          listItems.length === selectedListItems.length
        : excludedListItems.length === 0,
    listSelectMode: mode,
    resetListSelect,
    selectedListItems,
    updateListItems: setListItemsState,
    updateListSelectMode,
    updateSelectedListItem,
  };
};
