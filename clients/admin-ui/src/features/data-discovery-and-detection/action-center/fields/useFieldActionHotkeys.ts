import { useMessage } from "fidesui";
import { useHotkeys } from "react-hotkeys-hook";

import { DiffStatus } from "~/types/api/models/DiffStatus";
import { FieldActionType } from "~/types/api/models/FieldActionType";

import {
  ACTION_ALLOWED_STATUSES,
  ACTIONS_DISABLED_MESSAGE,
  FIELD_ACTION_HOTKEYS,
} from "./FieldActions.const";
import { MonitorResource } from "./types";
import { useFieldActions } from "./useFieldActions";

// DOM selectors for category select components
const SELECTORS = {
  DRAWER_OPEN: ".ant-drawer-open",
  DRAWER_SELECT: ".ant-drawer-open .ant-select",
  SELECT: ".ant-select",
  SELECT_SELECTOR: ".ant-select-selector",
  SELECT_DISABLED: "ant-select-disabled",
  INPUT: "input",
  LIST_ITEM_SELECT: "[data-classification-select]",
} as const;

type ActiveListItem = MonitorResource | null;

/**
 * Hook to handle keyboard shortcuts for field actions in the Action Center
 * @param activeListItem - The currently active list item
 * @param fieldActions - The field actions object from useFieldActions
 * @param updateSelectedListItem - Function to update the selected list item
 * @param onNavigate - Function to handle navigation to field details
 * @param isDrawerOpen - Whether the details drawer is currently open
 * @param onRefresh - Function to handle refreshing the list
 */
export const useFieldActionHotkeys = (
  activeListItem: ActiveListItem | undefined,
  fieldActions: ReturnType<typeof useFieldActions>,
  updateSelectedListItem: (key: React.Key, selected: boolean) => void,
  onNavigate: (urn: string | undefined) => void,
  isDrawerOpen: boolean,
  onRefresh: () => void,
) => {
  const messageApi = useMessage();
  // Helper to open a category select dropdown programmatically
  const openCategorySelect = (selectElement: Element): boolean => {
    const selectorElement = selectElement.querySelector(
      SELECTORS.SELECT_SELECTOR,
    ) as HTMLElement;

    if (!selectorElement) {
      return false;
    }

    // Check if the select is disabled
    const isDisabled = selectElement.classList.contains(
      SELECTORS.SELECT_DISABLED,
    );

    if (isDisabled) {
      messageApi.warning(
        "You cannot assign categories to this resource in its current state",
      );
      return false;
    }

    // Dispatch a mousedown event to trigger the dropdown
    const mousedownEvent = new MouseEvent("mousedown", {
      bubbles: true,
      cancelable: true,
      view: window,
    });
    selectorElement.dispatchEvent(mousedownEvent);

    // Focus the input to ensure proper keyboard navigation
    const inputElement = selectElement.querySelector(
      SELECTORS.INPUT,
    ) as HTMLInputElement;
    if (inputElement) {
      inputElement.focus();
    }

    return true;
  };

  // Helper to handle hotkey actions on focused item
  const handleHotkeyAction = (
    actionType:
      | FieldActionType.APPROVE
      | FieldActionType.PROMOTE
      | FieldActionType.MUTE
      | FieldActionType.UN_MUTE,
  ) => {
    if (!activeListItem) {
      return;
    }

    const isActionAvailable =
      activeListItem.diff_status &&
      (ACTION_ALLOWED_STATUSES[actionType] as readonly DiffStatus[])?.includes(
        activeListItem.diff_status,
      );

    if (isActionAvailable) {
      fieldActions[actionType]([activeListItem.urn]);
    } else {
      messageApi.warning(ACTIONS_DISABLED_MESSAGE[actionType]);
    }
  };

  useHotkeys(
    FIELD_ACTION_HOTKEYS.APPROVE,
    () => handleHotkeyAction(FieldActionType.APPROVE),
    [activeListItem, fieldActions],
  );

  useHotkeys(
    FIELD_ACTION_HOTKEYS.PROMOTE,
    () => handleHotkeyAction(FieldActionType.PROMOTE),
    [activeListItem, fieldActions],
  );

  useHotkeys(
    FIELD_ACTION_HOTKEYS.MUTE,
    () => handleHotkeyAction(FieldActionType.MUTE),
    [activeListItem, fieldActions],
  );

  useHotkeys(FIELD_ACTION_HOTKEYS.REFRESH, () => onRefresh(), [onRefresh]);

  useHotkeys(
    FIELD_ACTION_HOTKEYS.TOGGLE_DRAWER,
    () => {
      if (activeListItem && isDrawerOpen) {
        onNavigate(undefined);
      } else if (activeListItem && !isDrawerOpen) {
        onNavigate(activeListItem.urn);
      }
    },
    [activeListItem, onNavigate, isDrawerOpen],
  );

  useHotkeys(
    FIELD_ACTION_HOTKEYS.OPEN_CLASSIFICATION_SELECT,
    (e) => {
      e.preventDefault();

      if (!activeListItem) {
        return;
      }

      let categorySelect: Element | null = null;

      // If drawer is open, target the DataCategorySelect in the drawer
      if (isDrawerOpen) {
        const drawer = document.querySelector(SELECTORS.DRAWER_OPEN);
        if (drawer) {
          // DataCategorySelect in drawer doesn't have data-classification-select attribute
          categorySelect = drawer.querySelector(SELECTORS.SELECT);
        }
      } else {
        // Otherwise, target the ClassificationSelect for the active list item
        // Use CSS.escape to properly escape the URN value for use in CSS selector
        const escapedUrn = CSS.escape(activeListItem.urn);
        categorySelect = document.querySelector(
          `[data-classification-select="${escapedUrn}"]`,
        );
      }

      if (categorySelect) {
        openCategorySelect(categorySelect);
      }
    },
    [activeListItem, messageApi, isDrawerOpen],
  );

  // Handle escape key to blur category selects and restore list navigation
  useHotkeys(
    "escape",
    (e) => {
      const focusedElement = document.activeElement as HTMLElement;

      if (focusedElement?.tagName !== "INPUT") {
        return;
      }

      // Check if a category select input is focused (either in list or drawer)
      const isListItemSelect = focusedElement.closest(
        SELECTORS.LIST_ITEM_SELECT,
      );
      const isDrawerSelect = focusedElement.closest(SELECTORS.DRAWER_SELECT);

      if (isListItemSelect || isDrawerSelect) {
        e.preventDefault();
        e.stopPropagation();
        // Blur the input to close the dropdown and return focus
        focusedElement.blur();
      }
    },
    { enableOnFormTags: ["INPUT"] },
    [isDrawerOpen],
  );
};
