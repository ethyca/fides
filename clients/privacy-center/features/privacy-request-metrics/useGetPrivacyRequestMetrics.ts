import { MOCK_METRICS } from "./mock-data";
import type { PrivacyRequestMetricsResponse } from "./types";

interface UseGetPrivacyRequestMetricsResult {
  data: PrivacyRequestMetricsResponse;
  isLoading: boolean;
  isError: boolean;
}

export const useGetPrivacyRequestMetrics =
  (): UseGetPrivacyRequestMetricsResult => {
    return { data: MOCK_METRICS, isLoading: false, isError: false };
  };
