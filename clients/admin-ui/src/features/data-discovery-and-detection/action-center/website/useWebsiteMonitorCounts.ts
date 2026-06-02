import { UNCATEGORIZED_SEGMENT } from "~/features/common/nav/routes";
import { DiffStatus } from "~/types/api";

import { useGetDiscoveredAssetsQuery } from "../action-center.slice";
import { DiscoveryErrorStatuses } from "../constants";

/**
 * Derives the website monitor's labeled / unlabeled / compliance-issue counts
 * ("by system" semantics) from two lightweight count queries. These aren't part
 * of the per-monitor aggregate `updates` payload, so they're fetched here and
 * shared by the root subheader and the findings cards (RTK dedupes the calls).
 */
export const useWebsiteMonitorCounts = (
  monitorId: string,
  totalAdditions: number,
) => {
  const { data: uncategorized } = useGetDiscoveredAssetsQuery(
    {
      key: monitorId,
      system: UNCATEGORIZED_SEGMENT,
      diff_status: [DiffStatus.ADDITION],
      page: 1,
      size: 1,
    },
    { skip: !monitorId },
  );

  const { data: compliance } = useGetDiscoveredAssetsQuery(
    {
      key: monitorId,
      diff_status: [DiffStatus.ADDITION],
      consent_aggregated: [...DiscoveryErrorStatuses],
      page: 1,
      size: 1,
    },
    { skip: !monitorId },
  );

  const unlabeled = uncategorized?.total ?? 0;
  const labeled = Math.max(0, totalAdditions - unlabeled);
  const complianceIssues = compliance?.total ?? 0;

  return { labeled, unlabeled, complianceIssues };
};
