import { useGetPrivacyRequestMetricsQuery } from "./privacy-request-metrics.slice";
import type { PrivacyRequestMetricsResponse } from "./types";

interface UseGetPrivacyRequestMetricsResult {
  data: PrivacyRequestMetricsResponse | undefined;
  isLoading: boolean;
  isError: boolean;
}

export const useGetPrivacyRequestMetrics = (
  location?: string,
): UseGetPrivacyRequestMetricsResult => {
  const { data, isLoading, isError } = useGetPrivacyRequestMetricsQuery(
    location ? { location } : undefined,
  );
  return { data, isLoading, isError };
};
