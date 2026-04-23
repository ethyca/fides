import { useGetPrivacyRequestMetricsQuery } from "./privacy-request-metrics.slice";
import type { PrivacyRequestMetricsResponse } from "./types";

/**
 * Get the previous calendar year date range for CCPA/CPRA reporting.
 */
function getPreviousCalendarYear() {
  const year = new Date().getFullYear() - 1;
  return {
    start_date: `${year}-01-01`,
    end_date: `${year}-12-31`,
  };
}

interface UseGetPrivacyRequestMetricsResult {
  data: PrivacyRequestMetricsResponse | undefined;
  isLoading: boolean;
  isError: boolean;
}

/**
 * Fetches CCPA/CPRA disclosure metrics for California.
 * The location is hardcoded to "us_ca" since the disclosure requirement
 * is California-specific
 */
export const useGetPrivacyRequestMetrics =
  (): UseGetPrivacyRequestMetricsResult => {
    const dateRange = getPreviousCalendarYear();
    const { data, isLoading, isError } = useGetPrivacyRequestMetricsQuery({
      ...dateRange,
      location: "us_ca",
    });
    return { data, isLoading, isError };
  };
