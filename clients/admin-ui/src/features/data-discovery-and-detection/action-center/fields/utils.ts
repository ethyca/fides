import type { ModalFuncProps } from "antd/es/modal";
import type { ReactNode } from "react";

import { Severity } from "~/features/common/progress/SeverityGauge/types";
import { pluralize } from "~/features/common/utils";
import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";
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

const CONFIDENCE_BUCKET_TO_SEVERITY: Record<
  ConfidenceBucket,
  Severity | undefined
> = {
  high: "high",
  medium: "medium",
  low: "low",
  manual: undefined,
} as const;

export function mapConfidenceBucketToSeverity(
  confidenceBucket: ConfidenceBucket,
): Severity | undefined {
  return CONFIDENCE_BUCKET_TO_SEVERITY[confidenceBucket];
}

export const getMaxSeverity = (
  severityList: Severity[],
): Severity | undefined => {
  return severityList.reduce(
    (agg, current) => {
      switch (agg) {
        case "high":
          return agg;
        case "medium":
          return current === "high" ? current : agg;
        default:
          return current || agg;
      }
    },
    undefined as Severity | undefined,
  );
};
