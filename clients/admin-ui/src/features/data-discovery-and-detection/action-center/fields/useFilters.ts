import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringEnum,
  parseAsStringLiteral,
  useQueryState,
} from "nuqs";

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
  };
};
