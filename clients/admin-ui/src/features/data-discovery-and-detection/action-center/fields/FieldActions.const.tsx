import type { ModalFuncProps } from "antd/es/modal";
import { Icons, SparkleIcon } from "fidesui";
import { ReactNode } from "react";

import { pluralize } from "~/features/common/utils";
import { DiffStatus } from "~/types/api";
import { FieldActionType } from "~/types/api/models/FieldActionType";

import { FieldActionTypeValue } from "./types";

const { REVIEW, CLASSIFY, PROMOTE, MUTE, UN_MUTE, PROMOTE_REMOVALS } =
  FieldActionType;

export const FIELD_ACTION_LABEL: Record<FieldActionTypeValue, string> = {
  review: "Mark as reviewed",
  "assign-categories": "Assign categories",
  classify: "Classify",
  mute: "Ignore",
  promote: "Approve",
  "promote-removals": "Remove",
  "un-review": "Un-mark as reviewed",
  "un-mute": "Restore",
};

/** TODO: fix all */
export const FIELD_ACTION_INTERMEDIATE: Record<FieldActionTypeValue, string> = {
  review: "Marking as reviewed",
  "assign-categories": "Updating data categories",
  classify: "Classifying",
  mute: "Ignoring",
  promote: "Approving",
  "promote-removals": "Removing",
  "un-review": "Un-marking as reviewed",
  "un-mute": "Restoring",
};

export const FIELD_ACTION_COMPLETED: Record<FieldActionTypeValue, string> = {
  review: "Marked as reviewed",
  "assign-categories": "Data category updated",
  classify: "Classified",
  mute: "Ignored",
  promote: "Approved",
  "promote-removals": "Removed",
  "un-review": "Un-marked as reviewed",
  "un-mute": "Restored",
};

export const DEFAULT_DRAWER_ACTIONS = [REVIEW, PROMOTE] as const;

export const DRAWER_ACTIONS = {
  addition: DEFAULT_DRAWER_ACTIONS,
  reviewed: DEFAULT_DRAWER_ACTIONS,
  classification_addition: DEFAULT_DRAWER_ACTIONS,
  classification_error: DEFAULT_DRAWER_ACTIONS,
  classification_queued: DEFAULT_DRAWER_ACTIONS,
  classification_update: DEFAULT_DRAWER_ACTIONS,
  classifying: DEFAULT_DRAWER_ACTIONS,
  monitored: DEFAULT_DRAWER_ACTIONS,
  muted: [UN_MUTE],
  promoting: DEFAULT_DRAWER_ACTIONS,
  promotion_error: DEFAULT_DRAWER_ACTIONS,
  removal: [MUTE, PROMOTE_REMOVALS],
  removal_promotion_error: [MUTE, PROMOTE_REMOVALS],
  removing: [MUTE, PROMOTE_REMOVALS],
} as const satisfies Readonly<
  Record<DiffStatus, ReadonlyArray<FieldActionType>>
>;

export const DROPDOWN_ACTIONS = [
  CLASSIFY,
  REVIEW,
  PROMOTE,
  MUTE,
  UN_MUTE,
  PROMOTE_REMOVALS,
] as const;

export const RESOURCE_ACTIONS = [
  PROMOTE_REMOVALS,
  CLASSIFY,
  MUTE,
  UN_MUTE,
] as const;

export const DEFAULT_LIST_ITEM_ACTIONS = [CLASSIFY, PROMOTE] as const;

export const LIST_ITEM_ACTIONS = {
  addition: DEFAULT_LIST_ITEM_ACTIONS,
  reviewed: DEFAULT_LIST_ITEM_ACTIONS,
  classification_addition: DEFAULT_LIST_ITEM_ACTIONS,
  classification_error: DEFAULT_LIST_ITEM_ACTIONS,
  classification_queued: DEFAULT_LIST_ITEM_ACTIONS,
  classification_update: DEFAULT_LIST_ITEM_ACTIONS,
  classifying: DEFAULT_LIST_ITEM_ACTIONS,
  monitored: DEFAULT_LIST_ITEM_ACTIONS,
  muted: [UN_MUTE],
  promoting: DEFAULT_LIST_ITEM_ACTIONS,
  promotion_error: DEFAULT_LIST_ITEM_ACTIONS,
  removal: [PROMOTE_REMOVALS],
  removal_promotion_error: [PROMOTE_REMOVALS],
  removing: [PROMOTE_REMOVALS],
} as const satisfies Readonly<
  Record<DiffStatus, ReadonlyArray<FieldActionType>>
>;

export const ACTIONS_DISABLED_MESSAGE: Record<
  (typeof DROPDOWN_ACTIONS)[number],
  string
> = {
  [REVIEW]:
    "You can only mark resources as reviewed with a data category applied",
  [CLASSIFY]:
    "You cannot classify resources that are already in classification or ignored",
  [MUTE]: "You cannot ignore resources that are already ignored",
  [PROMOTE]: "You can only approve resources that have a data category applied",
  [UN_MUTE]: "You can only restore resources that are ignored",
  [PROMOTE_REMOVALS]:
    "You can only remove resources that are in a removed status",
};

/**
 * Enum that exists in fidesplus. Keep in sync for correct logic
 */
export const ACTION_ALLOWED_STATUSES = {
  classify: [
    DiffStatus.ADDITION,
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
    DiffStatus.CLASSIFICATION_ERROR,
  ],
  review: [
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
    DiffStatus.REVIEWED,
  ],
  "un-review": [DiffStatus.REVIEWED],
  promote: [
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
    DiffStatus.REVIEWED,
    DiffStatus.PROMOTION_ERROR,
  ],
  "promote-removals": [DiffStatus.REMOVAL, DiffStatus.REMOVAL_PROMOTION_ERROR],
  mute: [
    DiffStatus.ADDITION,
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
    DiffStatus.REVIEWED,
    DiffStatus.REMOVAL,
    DiffStatus.CLASSIFICATION_ERROR,
    DiffStatus.PROMOTION_ERROR,
    DiffStatus.REMOVAL_PROMOTION_ERROR,
  ],
  "un-mute": [DiffStatus.MUTED],
  "assign-categories": [
    DiffStatus.ADDITION,
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
    DiffStatus.REVIEWED,
    DiffStatus.CLASSIFICATION_ERROR,
    DiffStatus.PROMOTION_ERROR,
  ],
} as const satisfies Readonly<
  Record<FieldActionType, Readonly<Array<DiffStatus>>>
>;

export const FIELD_ACTION_ICON = {
  "assign-categories": null,
  "promote-removals": <Icons.TrashCan />,
  "un-review": null,
  "un-mute": <Icons.View />,
  review: <Icons.Checkmark />,
  classify: <SparkleIcon size={14} />,
  mute: <Icons.ViewOff />,
  promote: <Icons.Checkmark />,
} as const satisfies Readonly<Record<FieldActionType, ReactNode>>;

export const FIELD_ACTION_HOTKEYS = {
  REVIEW: "r",
  PROMOTE: "a",
  MUTE: "i",
  UN_MUTE: "z",
  REFRESH: ".",
  TOGGLE_DRAWER: "o",
  OPEN_CLASSIFICATION_SELECT: "e",
} as const;

export const FIELD_ACTION_CONFIRMATION_MESSAGE = {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  "assign-categories": (_targetItemCount: number) => null,
  "promote-removals": (targetItemCount: number) =>
    `Are you sure you want to remove ${targetItemCount.toLocaleString()} ${pluralize(targetItemCount, "resource", "resources")}?`,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  "un-review": (_targetItemCount: number) => null,
  "un-mute": (targetItemCount: number) =>
    `Are you sure you want to restore ${targetItemCount.toLocaleString()} ${pluralize(targetItemCount, "resource", "resources")}?`,
  review: (targetItemCount: number) =>
    `Are you sure you want to mark ${targetItemCount.toLocaleString()} ${pluralize(targetItemCount, "resource", "resources")} as reviewed?`,
  classify: (targetItemCount: number) =>
    `Are you sure you want to run the classifier and apply data categories to ${targetItemCount.toLocaleString()} unlabeled ${pluralize(targetItemCount, "resource", "resources")}?`,
  mute: (targetItemCount: number) =>
    `Are you sure you want to ignore ${targetItemCount.toLocaleString()} ${pluralize(targetItemCount, "resource", "resources")}? After ignoring, these resources may reappear in future scans.`,
  promote: (targetItemCount: number) =>
    `Are you sure you want to approve ${targetItemCount.toLocaleString()} ${pluralize(targetItemCount, "resource", "resources")}? After approving this data can be used for policy automation and DSRs. `,
} as const satisfies Readonly<
  Record<FieldActionType, (targetItemCount: number) => ReactNode>
>;

export const DEFAULT_CONFIRMATION_PROPS: ModalFuncProps = {
  onCancel: async () => false,
  onOk: async () => true,
  icon: null,
  /* TODO: standardize */
  width: 542,
};
