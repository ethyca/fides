import { CheckboxProps } from "fidesui";
import _ from "lodash";
import { Key, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

import type { Node } from "~/features/common/hooks/useNodeMap";

export const BULK_LIST_HOTKEYS = {
  SELECT_ALL: "h",
  DESELECT_ALL: "l",
  TOGGLE_SELECTION: "space",
} as const;

type SelectMode = "inclusive" | "exclusive";

export const extractListItemKeys = <T>(data: Array<Node<T>>) =>
  data.map(({ key }) => key);

interface UseBulkListSelectOptions<T> {
  activeListItem?: Node<T> | null;
  enableKeyboardShortcuts?: boolean;
}

export const useBulkListSelect = <T>(
  listKeys: Key[] | undefined,
  options: UseBulkListSelectOptions<T> = {},
  initialMode: SelectMode = "inclusive",
) => {
  const { activeListItem = null, enableKeyboardShortcuts = false } = options;

  const [mode, setMode] = useState<SelectMode>(initialMode);
  /**
   * Delta between selected vs non-selected elements
   * includes selected elements when in inclusive mode
   * will be deselected elements when in exclusive mode
   */
  const [deltaKeys, setDeltaKeysState] = useState<Key[]>([]);

  const updateSelectedListItem = (key: React.Key, isSelected: boolean) => {
    const updateMode: "add" | "remove" = (
      mode === "inclusive" ? isSelected : !isSelected
    )
      ? "add"
      : "remove";

    switch (updateMode) {
      case "add":
        setDeltaKeysState([...deltaKeys, key]);
        break;
      default:
        setDeltaKeysState(deltaKeys.filter((k) => k !== key));
    }
  };

  const updateListSelectMode = (newMode: SelectMode) => {
    setMode(newMode);
    setDeltaKeysState([]);
  };

  const resetListSelect = () => {
    setDeltaKeysState([]);
    setMode("inclusive");
  };

  const inverseDeltaKeys = _.difference(listKeys, deltaKeys);

  const selectedKeys = mode === "inclusive" ? deltaKeys : inverseDeltaKeys;
  const excludedKeys = mode === "exclusive" ? deltaKeys : inverseDeltaKeys;

  // Note: Activation hotkeys (j, k, escape) are handled by CustomList component
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
    BULK_LIST_HOTKEYS.TOGGLE_SELECTION,
    (e) => {
      if (activeListItem) {
        e.preventDefault(); // Prevent page scroll
        const isSelected = selectedKeys.includes(activeListItem.key);
        updateSelectedListItem(activeListItem.key, !isSelected);
      }
    },
    { enabled: enableKeyboardShortcuts },
    [activeListItem, selectedKeys, updateSelectedListItem],
  );

  const checkboxProps: CheckboxProps = {
    checked:
      mode === "inclusive"
        ? selectedKeys.length > 0 && listKeys?.length === selectedKeys.length
        : excludedKeys.length === 0,
    indeterminate:
      mode === "inclusive"
        ? selectedKeys.length > 0 && listKeys?.length !== selectedKeys.length
        : excludedKeys.length > 0,
    onChange: (e) =>
      updateListSelectMode(e.target.checked ? "exclusive" : "inclusive"),
  };

  return {
    checkboxProps,
    excludedKeys,
    listSelectMode: mode,
    resetListSelect,
    selectedKeys,
    updateListSelectMode,
    updateSelectedListItem,
  };
};
