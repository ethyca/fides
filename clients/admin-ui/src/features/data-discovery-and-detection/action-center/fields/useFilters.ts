import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringEnum,
  parseAsStringLiteral,
  useQueryState,
} from "nuqs";
import { useEffect } from "react";

import { ConfidenceScoreRange } from "~/types/api/models/ConfidenceScoreRange";

import { RESOURCE_STATUS } from "./MonitorFields.const";

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
  useEffect(() => {
    if (resourceStatus === null) {
      const defaultStatuses = RESOURCE_STATUS.filter(
        (status) => status !== "Confirmed" && status !== "Ignored",
      );
      setResourceStatus(defaultStatuses);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  const resetToInitialState = () => {
    const defaultStatuses = RESOURCE_STATUS.filter(
      (status) => status !== "Confirmed" && status !== "Ignored",
    );
    setResourceStatus(defaultStatuses);
    setConfidenceScore(null);
    setDataCategory(null);
  };

  const reset = () => {
    setResourceStatus(null);
    setConfidenceScore(null);
    setDataCategory(null);
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
