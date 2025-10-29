import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringEnum,
  parseAsStringLiteral,
  useQueryState,
} from "nuqs";
import { useEffect } from "react";

import { ConfidenceScoreRange } from "~/types/api/models/ConfidenceScoreRange";

import { getFilterableStatuses, RESOURCE_STATUS } from "./MonitorFields.const";

export const useMonitorFieldsFilters = () => {
  const [resourceStatus, setResourceStatus] = useQueryState(
    "resourceStatus",
    parseAsArrayOf(parseAsStringLiteral(RESOURCE_STATUS)),
  );
  const [confidenceScore, setConfidenceScore] = useQueryState(
    "confidenceScore",
    parseAsArrayOf(
      parseAsStringEnum<ConfidenceScoreRange>(
        Object.values(ConfidenceScoreRange),
      ),
    ),
  );
  const [dataCategory, setDataCategory] = useQueryState(
    "dataCategory",
    parseAsArrayOf(parseAsString),
  );

  // Set initial state: preselect all statuses except "Confirmed" and "Ignored"
  // Only run if resourceStatus is explicitly null (not initialized)
  // Once initialized, an empty array [] means "no filters" (different from null)
  useEffect(() => {
    if (resourceStatus === null) {
      const defaultStatuses = getFilterableStatuses([...RESOURCE_STATUS]);
      // Use empty array if no valid defaults, not null
      setResourceStatus(defaultStatuses.length > 0 ? defaultStatuses : []);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount, or we could get in an infinite loop if all items are filtered out

  const resetToInitialState = () => {
    const defaultStatuses = getFilterableStatuses([...RESOURCE_STATUS]);
    setResourceStatus(defaultStatuses);
    setConfidenceScore(null);
    setDataCategory(null);
  };

  const reset = () => {
    // Use empty array instead of null to indicate "no filters selected"
    // null is reserved for "not yet initialized"
    setResourceStatus([]);
    setConfidenceScore([]);
    setDataCategory([]);
  };

  return {
    resourceStatus,
    setResourceStatus,
    confidenceScore,
    setConfidenceScore,
    dataCategory,
    setDataCategory,
    reset,
    resetToInitialState,
  };
};
