import type { ModalFuncProps } from "antd/es/modal";
import type { ReactNode } from "react";

import { Severity } from "~/features/common/progress/SeverityGauge/types";
import { pluralize } from "~/features/common/utils";
import { DiffStatus } from "~/types/api";
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

export const getActionErrorMessage = (actionType: FieldActionType) => {
  const activityTabSuffix =
    actionType === FieldActionType.CLASSIFY ||
    actionType === FieldActionType.PROMOTE
      ? ": View summary in the activity tab"
      : "";
  return `Action failed${activityTabSuffix}`;
};

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

export enum InfrastructureStatusFilterOptionValue {
  NEW = "new",
  KNOWN = "known",
  UNKNOWN = "unknown",
  IGNORED = "ignored",
}

export const INFRASTRUCTURE_STATUS_FILTER_MAP: Record<
  InfrastructureStatusFilterOptionValue,
  { diffStatusFilter: DiffStatus[]; vendorIdFilter: string[] }
> = {
  [InfrastructureStatusFilterOptionValue.NEW]: {
    diffStatusFilter: [DiffStatus.ADDITION],
    vendorIdFilter: [],
  },
  [InfrastructureStatusFilterOptionValue.KNOWN]: {
    diffStatusFilter: [DiffStatus.ADDITION],
    vendorIdFilter: ["known"],
  },
  [InfrastructureStatusFilterOptionValue.UNKNOWN]: {
    diffStatusFilter: [DiffStatus.ADDITION],
    vendorIdFilter: ["unknown"],
  },
  [InfrastructureStatusFilterOptionValue.IGNORED]: {
    diffStatusFilter: [DiffStatus.MUTED],
    vendorIdFilter: [],
  },
};

export const parseFiltersToFilterValue = (
  statusFilters: string[],
  vendorFilters: string[],
): InfrastructureStatusFilterOptionValue | undefined => {
  if (vendorFilters.includes("known")) {
    return InfrastructureStatusFilterOptionValue.KNOWN;
  }
  if (vendorFilters.includes("unknown")) {
    return InfrastructureStatusFilterOptionValue.UNKNOWN;
  }
  if (statusFilters.includes(DiffStatus.ADDITION)) {
    return InfrastructureStatusFilterOptionValue.NEW;
  }
  if (statusFilters.includes(DiffStatus.MUTED)) {
    return InfrastructureStatusFilterOptionValue.IGNORED;
  }
  return undefined;
};
