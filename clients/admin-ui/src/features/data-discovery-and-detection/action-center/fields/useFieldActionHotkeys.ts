import { AntMessage as Message } from "fidesui";
import { useHotkeys } from "react-hotkeys-hook";

import { DatastoreStagedResourceAPIResponse } from "~/types/api/models/DatastoreStagedResourceAPIResponse";
import { DiffStatus } from "~/types/api/models/DiffStatus";
import { FieldActionType } from "~/types/api/models/FieldActionType";

import {
  ACTION_ALLOWED_STATUSES,
  ACTIONS_DISABLED_MESSAGE,
  FIELD_ACTION_HOTKEYS,
} from "./FieldActions.const";
import { useFieldActions } from "./useFieldActions";

type ActiveListItem =
  | (DatastoreStagedResourceAPIResponse & {
      itemKey: React.Key;
    })
  | null;

/**
 * Hook to handle keyboard shortcuts for field actions in the Action Center
 * @param activeListItem - The currently active list item
 * @param fieldActions - The field actions object from useFieldActions
 * @param updateSelectedListItem - Function to update the selected list item
 * @param onNavigate - Function to handle navigation to field details
 * @param messageApi - Ant Design message API instance (needs to be passed in to avoid re-rendering the hook)
 */
export const useFieldActionHotkeys = (
  activeListItem: ActiveListItem,
  fieldActions: ReturnType<typeof useFieldActions>,
  updateSelectedListItem: (itemKey: React.Key, selected: boolean) => void,
  onNavigate: (urn: string) => void,
  messageApi: ReturnType<typeof Message.useMessage>[0],
) => {
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
      // Simulate selecting the item and calling the action
      updateSelectedListItem(activeListItem.itemKey, true);
      fieldActions[actionType]([activeListItem.urn]);
    } else {
      // Show the disabled tooltip message
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

  useHotkeys(
    FIELD_ACTION_HOTKEYS.UN_MUTE,
    () => handleHotkeyAction(FieldActionType.UN_MUTE),
    [activeListItem, fieldActions],
  );

  useHotkeys(
    FIELD_ACTION_HOTKEYS.OPEN_DRAWER,
    () => {
      if (activeListItem) {
        onNavigate(activeListItem.urn);
      }
    },
    [activeListItem, onNavigate],
  );
};
