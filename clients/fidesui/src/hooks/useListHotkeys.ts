import { useEffect, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

/**
 * Keyboard shortcuts for list navigation and selection
 */
export const LIST_HOTKEYS = {
  NAVIGATE_UP: "k",
  NAVIGATE_DOWN: "j",
  TOGGLE_SELECTION: "space",
  CLEAR_FOCUS: "escape",
} as const;

interface UseListHotkeysOptions {
  itemCount: number;
  selectedKeys: React.Key[];
  onToggleSelection?: (key: React.Key, checked: boolean) => void;
  getItemKey: (index: number) => React.Key;
  listId: string;
  enabled?: boolean;
}

/**
 * Custom hook that provides keyboard navigation and selection for lists.
 * Handles focus management, scroll-into-view, and keyboard shortcuts.
 *
 * @param itemCount - Total number of items in the list
 * @param selectedKeys - Selected item keys
 * @param onToggleSelection - Optional callback to toggle selection of an item by key (space is disabled if not provided)
 * @param getItemKey - Get the key for an item at a specific index
 * @param listId - Unique list ID for data attribute selector
 * @param enabled - Whether keyboard shortcuts are enabled
 *
 * Keyboard shortcuts:
 * - j: Navigate down (next item)
 * - k: Navigate up (previous item)
 * - space: Toggle selection of focused item (only if onToggleSelection is provided)
 * - escape: Clear focus
 */
export const useListHotkeys = ({
  itemCount,
  selectedKeys,
  onToggleSelection,
  getItemKey,
  listId,
  enabled = false,
}: UseListHotkeysOptions) => {
  const [activeListItemIndex, setActiveListItemIndex] = useState<number | null>(
    null,
  );

  useEffect(() => {
    if (activeListItemIndex !== null && activeListItemIndex >= itemCount) {
      // If items are filtered/removed, the focused index could be out of bounds, so we clear it
      setActiveListItemIndex(null);
    }
  }, [itemCount, activeListItemIndex]);

  // Scroll focused item into view
  useEffect(() => {
    if (activeListItemIndex !== null) {
      const element = document.querySelector(
        `[data-listitem="${listId}-${activeListItemIndex}"]`,
      );
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }
  }, [activeListItemIndex, listId]);

  // Navigate up (previous item)
  useHotkeys(
    LIST_HOTKEYS.NAVIGATE_UP,
    () => {
      if (itemCount > 0) {
        setActiveListItemIndex((prev) =>
          prev === null ? 0 : Math.max(prev - 1, 0),
        );
      }
    },
    { enabled },
    [itemCount],
  );

  // Navigate down (next item)
  useHotkeys(
    LIST_HOTKEYS.NAVIGATE_DOWN,
    () => {
      if (itemCount > 0) {
        setActiveListItemIndex((prev) =>
          prev === null ? 0 : Math.min(prev + 1, itemCount - 1),
        );
      }
    },
    { enabled },
    [itemCount],
  );

  // Clear focus
  useHotkeys(
    LIST_HOTKEYS.CLEAR_FOCUS,
    () => {
      setActiveListItemIndex(null);
    },
    { enabled },
  );

  // Toggle selection of focused item (only if onToggleSelection is provided)
  useHotkeys(
    LIST_HOTKEYS.TOGGLE_SELECTION,
    (e) => {
      if (
        onToggleSelection &&
        activeListItemIndex !== null &&
        activeListItemIndex < itemCount
      ) {
        e.preventDefault(); // Prevent page scroll
        const itemKey = getItemKey(activeListItemIndex);
        const isSelected = selectedKeys.includes(itemKey);
        onToggleSelection(itemKey, !isSelected);
      }
    },
    { enabled: enabled && !!onToggleSelection },
    [
      activeListItemIndex,
      itemCount,
      selectedKeys,
      getItemKey,
      onToggleSelection,
    ],
  );

  return {
    activeListItemIndex,
    setActiveListItemIndex,
  };
};
