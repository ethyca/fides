import { Icons, SparkleIcon } from "fidesui";
import { ReactNode } from "react";

import { FieldActionType } from "~/types/api/models/FieldActionType";

import { ResourceStatusLabel } from "./MonitorFields.const";
import { FieldActionTypeValue } from "./types";

export const FIELD_ACTION_LABEL: Record<FieldActionTypeValue, string> = {
  "assign-categories": "Assign categories",
  "promote-removals": "Promote removals",
  "un-approve": "Un-approve",
  "un-mute": "Restore",
  approve: "Approve",
  classify: "Classify",
  mute: "Ignore",
  promote: "Confirm",
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
