import { useGetPrivacyRequestMetricsQuery } from "./privacy-request-metrics.slice";
import type { PrivacyRequestMetricsResponse } from "./types";

interface UseGetPrivacyRequestMetricsResult {
  data: PrivacyRequestMetricsResponse | undefined;
  isLoading: boolean;
  isError: boolean;
}

export const useGetPrivacyRequestMetrics =
  (): UseGetPrivacyRequestMetricsResult => {
    const { data, isLoading, isError } = useGetPrivacyRequestMetricsQuery();
    return { data, isLoading, isError };
  };
