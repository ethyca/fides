import type { ModalFuncProps } from "antd/es/modal";
import type { ReactNode } from "react";

import { pluralize } from "~/features/common/utils";
import { FieldActionType } from "~/types/api/models/FieldActionType";

import {
  DEFAULT_CONFIRMATION_PROPS,
  FIELD_ACTION_COMPLETED,
} from "./FieldActions.const";

export const getActionModalProps = (
  verb: string,
  content: ReactNode,
): ModalFuncProps => ({
  title: verb,
  okText: verb,
  content,
  ...DEFAULT_CONFIRMATION_PROPS,
});

export const getActionSuccessMessage = (
  actionType: FieldActionType,
  itemCount?: number,
) =>
  `${FIELD_ACTION_COMPLETED[actionType]}${pluralize(itemCount ?? 0, "", `${actionType === FieldActionType.ASSIGN_CATEGORIES ? " for" : ""} ${itemCount?.toLocaleString()} resources`)}`;

export const getActionErrorMessage = (actionType: FieldActionType) =>
  `${FIELD_ACTION_COMPLETED[actionType]} failed${actionType === FieldActionType.CLASSIFY || actionType === FieldActionType.PROMOTE ? ": View summary in the activity tab" : ""}`;
