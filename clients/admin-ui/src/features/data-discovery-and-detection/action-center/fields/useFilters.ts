import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringLiteral,
  useQueryState,
} from "nuqs";

import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

import {
  DEFAULT_FILTER_STATUSES,
  RESOURCE_STATUS,
} from "./MonitorFields.const";

export const useMonitorFieldsFilters = () => {
  const [resourceStatus, setResourceStatus] = useQueryState(
    "resourceStatus",
    parseAsArrayOf(parseAsStringLiteral(RESOURCE_STATUS)).withDefault(
      DEFAULT_FILTER_STATUSES,
    ),
  );
  const [confidenceBucket, setConfidenceBucket] = useQueryState(
    "confidenceBucket",
    parseAsArrayOf(parseAsStringLiteral(Object.values(ConfidenceBucket))),
  );
  const [dataCategory, setDataCategory] = useQueryState(
    "dataCategory",
    parseAsArrayOf(parseAsString),
  );

  const resetToInitialState = () => {
    setResourceStatus(DEFAULT_FILTER_STATUSES);
    setConfidenceBucket(null);
    setDataCategory(null);
  };

  const reset = () => {
    // Use empty array instead of null to indicate "no filters selected"
    // null is reserved for "not yet initialized"
    setResourceStatus([]);
    setConfidenceBucket([]);
    setDataCategory([]);
  };

  return {
    resourceStatus,
    setResourceStatus,
    confidenceBucket,
    setConfidenceBucket,
    dataCategory,
    setDataCategory,
    reset,
    resetToInitialState,
  };
};
