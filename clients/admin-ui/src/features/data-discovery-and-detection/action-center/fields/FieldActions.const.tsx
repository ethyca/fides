import type { ModalFuncProps } from "antd/es/modal";
import { Icons, SparkleIcon } from "fidesui";
import { ReactNode } from "react";

import { FieldActionType } from "~/types/api/models/FieldActionType";

import { ResourceStatusLabel } from "./MonitorFields.const";
import { FieldActionTypeValue } from "./types";

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
  "assign-categories": "Adding data categories",
  classify: "Classifying",
  mute: "Ignoring",
  promote: "Confirming",
  "promote-removals": "Promoting removals",
  "un-approve": "Un-approving",
  "un-mute": "Restoring",
};

export const FIELD_ACTION_COMPLETED: Record<FieldActionTypeValue, string> = {
  approve: "Approved",
  "assign-categories": "Data category added",
  classify: "Classified",
  mute: "Ignored",
  promote: "Confirmed",
  "promote-removals": "Promoted removals",
  "un-approve": "Un-approved",
  "un-mute": "Restored",
};

export const DRAWER_ACTIONS = [
  FieldActionType.APPROVE,
  FieldActionType.PROMOTE,
] as const;
export const DROPDOWN_ACTIONS = [
  FieldActionType.CLASSIFY,
  FieldActionType.APPROVE,
  FieldActionType.PROMOTE,
  FieldActionType.MUTE,
  FieldActionType.UN_MUTE,
] as const;
export const LIST_ITEM_ACTIONS = [
  FieldActionType.CLASSIFY,
  FieldActionType.PROMOTE,
] as const;

export const AVAILABLE_ACTIONS = {
  "In Review": [
    FieldActionType.CLASSIFY,
    FieldActionType.MUTE,
    FieldActionType.APPROVE,
    FieldActionType.PROMOTE,
  ],
  Approved: [FieldActionType.MUTE, FieldActionType.PROMOTE],
  Classifying: [],
  Confirmed: [],
  Ignored: [FieldActionType.UN_MUTE],
  Removed: [],
  Unlabeled: [FieldActionType.ASSIGN_CATEGORIES, FieldActionType.CLASSIFY],
  "Confirming...": [],
} as const satisfies Readonly<
  Record<ResourceStatusLabel, Readonly<Array<FieldActionType>>>
>;

export const FIELD_ACTION_ICON = {
  "assign-categories": null,
  "promote-removals": null,
  "un-approve": null,
  "un-mute": <Icons.View />,
  approve: <Icons.Checkmark />,
  classify: <SparkleIcon />,
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
