import _ from "lodash";
import { useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

const BULK_LIST_HOTKEYS = {
  SELECT_ALL: "h",
  DESELECT_ALL: "l",
} as const;

type SelectMode = "inclusive" | "exclusive";

interface ListItem {
  itemKey: React.Key;
}

export const extractListItemKeys = <T extends ListItem>(data: Array<T>) =>
  data.map(({ itemKey }) => itemKey);

interface UseBulkListSelectOptions<T extends ListItem> {
  activeListItem?: T | null;
  enableKeyboardShortcuts?: boolean;
}

export const useBulkListSelect = <T extends ListItem>(
  options: UseBulkListSelectOptions<T> = {},
) => {
  const { activeListItem = null, enableKeyboardShortcuts } = options;
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

  // Keyboard shortcuts for bulk selection (select all / deselect all)
  // Note: Navigation shortcuts (j, k, space, escape) are handled by CustomList component
  useHotkeys(
    BULK_LIST_HOTKEYS.SELECT_ALL,
    () => {
      updateListSelectMode("exclusive");
    },
    { enabled: enableKeyboardShortcuts },
  );

  useHotkeys(
    BULK_LIST_HOTKEYS.DESELECT_ALL,
    () => {
      updateListSelectMode("inclusive");
    },
    { enabled: enableKeyboardShortcuts },
  );

  // Space hotkey to toggle selection of focused item
  // This provides the same functionality as CustomList's built-in space hotkey,
  // but works with custom checkbox implementations that don't use rowSelection
  useHotkeys(
    "space",
    (e) => {
      if (activeListItem) {
        e.preventDefault(); // Prevent page scroll
        const isSelected = selectedListItems.some(
          (item) => item.itemKey === activeListItem.itemKey,
        );
        updateSelectedListItem(activeListItem.itemKey, !isSelected);
      }
    },
    { enabled: enableKeyboardShortcuts },
    [activeListItem, selectedListItems, updateSelectedListItem],
  );

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
