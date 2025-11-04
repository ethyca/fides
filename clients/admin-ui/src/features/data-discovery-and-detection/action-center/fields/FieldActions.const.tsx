import type { ModalFuncProps } from "antd/es/modal";
import { Icons, SparkleIcon } from "fidesui";
import { ReactNode } from "react";

import { DiffStatus } from "~/types/api";
import { FieldActionType } from "~/types/api/models/FieldActionType";

import { FieldActionTypeValue } from "./types";

const { APPROVE, CLASSIFY, PROMOTE, MUTE, UN_MUTE } = FieldActionType;

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

export const ACTIONS_DISABLED_MESSAGE: Record<
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
  approve: [
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
    DiffStatus.APPROVED,
  ],
  "un-approve": [DiffStatus.APPROVED],
  promote: [
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
    DiffStatus.APPROVED,
    DiffStatus.PROMOTION_ERROR,
  ],
  "promote-removals": [DiffStatus.REMOVAL, DiffStatus.REMOVAL_PROMOTION_ERROR],
  mute: [
    DiffStatus.ADDITION,
    DiffStatus.CLASSIFICATION_ADDITION,
    DiffStatus.CLASSIFICATION_UPDATE,
    DiffStatus.APPROVED,
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
    DiffStatus.APPROVED,
    DiffStatus.CLASSIFICATION_ERROR,
    DiffStatus.PROMOTION_ERROR,
  ],
} as const satisfies Readonly<
  Record<FieldActionType, Readonly<Array<DiffStatus>>>
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

export const FIELD_ACTION_HOTKEYS = {
  APPROVE: "a",
  PROMOTE: "c",
  MUTE: "i",
  UN_MUTE: "r",
  OPEN_DRAWER: "o",
} as const;

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
