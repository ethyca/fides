import type { ModalFuncProps } from "antd/es/modal";
import { Icons, SparkleIcon } from "fidesui";
import { ReactNode } from "react";

import { DiffStatus } from "~/types/api";
import { FieldActionType } from "~/types/api/models/FieldActionType";

import { ResourceStatusLabel } from "./MonitorFields.const";
import { FieldActionTypeValue } from "./types";

const {
  APPROVE,
  CLASSIFY,
  PROMOTE,
  MUTE,
  UN_MUTE,
  PROMOTE_REMOVALS,
  ASSIGN_CATEGORIES,
} = FieldActionType;

export const FIELD_ACTION_LABEL: Record<FieldActionTypeValue, string> = {
  approve: "Approve",
  "assign-categories": "Assign categories",
  classify: "Classify",
  mute: "Ignore",
  promote: "Confirm",
  "promote-removals": "Promote removals",
  "un-approve": "Un-approve",
  "un-mute": "Restore",
};

/** TODO: fix all */
export const FIELD_ACTION_INTERMEDIATE: Record<FieldActionTypeValue, string> = {
  approve: "Approving",
  "assign-categories": "Updating data categories",
  classify: "Classifying",
  mute: "Ignoring",
  promote: "Confirming",
  "promote-removals": "Promoting removals",
  "un-approve": "Un-approving",
  "un-mute": "Restoring",
};

export const FIELD_ACTION_COMPLETED: Record<FieldActionTypeValue, string> = {
  approve: "Approved",
  "assign-categories": "Data category updated",
  classify: "Classified",
  mute: "Ignored",
  promote: "Confirmed",
  "promote-removals": "Promoted removals",
  "un-approve": "Un-approved",
  "un-mute": "Restored",
};

export const DRAWER_ACTIONS = [APPROVE, PROMOTE] as const;
export const DROPDOWN_ACTIONS = [
  CLASSIFY,
  APPROVE,
  PROMOTE,
  MUTE,
  UN_MUTE,
] as const;

export const LIST_ITEM_ACTIONS = [CLASSIFY, PROMOTE] as const;

export const DROPDOWN_ACTIONS_DISABLED_TOOLTIP: Record<
  (typeof DROPDOWN_ACTIONS)[number],
  string
> = {
  [APPROVE]: "You can only approve resources with a data category applied",
  [CLASSIFY]:
    "You cannot classify resources that are already in classification or ignored",
  [MUTE]: "You cannot ignore resources that are already ignored",
  [PROMOTE]: "You can only confirm resources that have a data category applied",
  [UN_MUTE]: "You can only restore resources that are ignored",
};

export const AVAILABLE_ACTIONS = {
  "In Review": [
    FieldActionType.CLASSIFY,
    FieldActionType.MUTE,
    FieldActionType.APPROVE,
    FieldActionType.PROMOTE,
    FieldActionType.ASSIGN_CATEGORIES,
  ],
  Approved: [
    FieldActionType.MUTE,
    FieldActionType.PROMOTE,
    FieldActionType.ASSIGN_CATEGORIES,
  ],
  Classifying: [],
  Confirmed: [],
  Ignored: [UN_MUTE],
  Removed: [],
  Unlabeled: [ASSIGN_CATEGORIES, CLASSIFY],
  "Confirming...": [],
  Error: [CLASSIFY, PROMOTE, PROMOTE_REMOVALS],
} as const satisfies Readonly<
  Record<ResourceStatusLabel, Readonly<Array<FieldActionType>>>
>;

export const DIFF_STATUS_TO_AVAILABLE_ACTIONS = {
  addition: AVAILABLE_ACTIONS.Unlabeled,
  approved: AVAILABLE_ACTIONS.Approved,
  classification_addition: AVAILABLE_ACTIONS["In Review"],
  classification_error: [CLASSIFY, MUTE, ASSIGN_CATEGORIES],
  classification_queued: AVAILABLE_ACTIONS.Classifying,
  classification_update: AVAILABLE_ACTIONS["In Review"],
  classifying: AVAILABLE_ACTIONS.Classifying,
  monitored: AVAILABLE_ACTIONS.Confirmed,
  muted: AVAILABLE_ACTIONS.Ignored,
  promoting: AVAILABLE_ACTIONS["Confirming..."],
  promotion_error: [PROMOTE, MUTE, ASSIGN_CATEGORIES],
  removal: AVAILABLE_ACTIONS.Removed,
  removing: AVAILABLE_ACTIONS["In Review"],
  removal_promotion_error: [PROMOTE_REMOVALS, MUTE],
} as const satisfies Readonly<
  Record<DiffStatus, Readonly<Array<FieldActionType>>>
>;

export const FIELD_ACTION_ICON = {
  "assign-categories": null,
  "promote-removals": null,
  "un-approve": null,
  "un-mute": <Icons.View />,
  approve: <Icons.Checkmark />,
  classify: <SparkleIcon size={14} />,
  mute: <Icons.ViewOff />,
  promote: <Icons.Checkmark />,
} as const satisfies Readonly<Record<FieldActionType, ReactNode>>;

export const FIELD_ACTION_CONFIRMATION_MESSAGE = {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  "assign-categories": (_targetItemCount: number) => null,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  "promote-removals": (_targetItemCount: number) => null,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  "un-approve": (_targetItemCount: number) => null,
  "un-mute": (targetItemCount: number) =>
    `Are you sure you want to restore ${targetItemCount.toLocaleString()} resources?`,
  approve: (targetItemCount: number) =>
    `Are you sure you want to approve ${targetItemCount.toLocaleString()} resources?`,
  classify: (targetItemCount: number) =>
    `Are you sure you want to run the classifier and apply data categories to ${targetItemCount.toLocaleString()} unlabeled resources?`,
  mute: (targetItemCount: number) =>
    `Are you sure you want to ignore ${targetItemCount.toLocaleString()} resources? After ignoring, these resources may reappear in future scans.`,
  promote: (targetItemCount: number) =>
    `Are you sure you want to confirm these ${targetItemCount.toLocaleString()} resources? After confirming this data can be used for policy automation and DSRs. `,
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
