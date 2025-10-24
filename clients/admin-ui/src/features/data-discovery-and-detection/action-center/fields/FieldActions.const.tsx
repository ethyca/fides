import { Icons, SparkleIcon } from "fidesui";
import { ReactNode } from "react";

import { FieldActionType } from "~/types/api/models/FieldActionType";

import { ResourceStatusLabel } from "./MonitorFields.const";
import { FieldActionTypeValue } from "./types";

export const FIELD_ACTION_LABEL: Record<FieldActionTypeValue, string> = {
  approve: "Approve",
  "assign-categories": "Assign categories",
  classify: "Classify",
  promote: "Confirm",
  "un-mute": "Un-mute",
  mute: "Ignore",
  "un-approve": "Un-approve",
  "promote-removals": "Promote removals",
};

export const AVAILABLE_ACTIONS = {
  Approved: [FieldActionType.MUTE, FieldActionType.PROMOTE],
  Unlabeled: [FieldActionType.ASSIGN_CATEGORIES, FieldActionType.CLASSIFY],
  Classifying: [],
  Confirmed: [],
  "In Review": [
    FieldActionType.MUTE,
    FieldActionType.APPROVE,
    FieldActionType.PROMOTE,
  ],
  Ignored: [FieldActionType.UN_MUTE],
  Removed: [],
} as const satisfies Readonly<
  Record<ResourceStatusLabel, Readonly<Array<FieldActionType>>>
>;

export const FIELD_ACTION_ICON = {
  mute: <Icons.ViewOff />,
  approve: <Icons.Checkmark />,
  classify: <SparkleIcon />,
  "un-mute": <Icons.View />,
  promote: <Icons.Checkmark />,
  "assign-categories": null,
  "un-approve": null,
  "promote-removals": null,
} as const satisfies Readonly<Record<FieldActionType, ReactNode>>;
