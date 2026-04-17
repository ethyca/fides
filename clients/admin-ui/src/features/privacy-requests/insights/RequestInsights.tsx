import classNames from "classnames";
import { Divider, Flex } from "fidesui";
import { parseAsString, useQueryStates } from "nuqs";
import { Fragment, useMemo } from "react";

import { useFlags } from "~/features/common/features";
import { useGetPrivacyRequestsQuery } from "~/features/dashboard/dashboard.slice";

import RequestProgressWidget from "./RequestProgressWidget";
import { pivotSlaHealthByBucket, SLA_BUCKET_ORDER } from "./utils";

/**
 * Top-of-page Helios-style insight row for the Request Manager (Lethe).
 *
 * Renders three cards, one per SLA bucket (On track / Approaching /
 * Overdue), separated by vertical dividers. The stacked bar and bottom
 * badges inside each card break the bucket's total down by DSR policy
 * action type — so a glance at "Overdue" shows not just how many are late
 * but also how that's distributed across access / erasure / consent /
 * update obligations.
 *
 * The widgets respond to the existing location filter on the page —
 * `PrivacyRequestFiltersBar` is the single source of truth. This
 * component reads the same URL-backed `location` param via `nuqs`, so
 * switching locations on the filter bar re-queries both the list below
 * and the insights above in sync. All gated by the shared
 * `heliosInsights` feature flag.
 */
const RequestInsights = () => {
  const {
    flags: { heliosInsights },
  } = useFlags();

  // Mirror the filter bar's location param (single source of truth lives in
  // `usePrivacyRequestsFilters`; reading the same URL key here avoids a
  // prop drill and a pagination dependency).
  const [{ location }] = useQueryStates({
    location: parseAsString,
  });

  const { data, isLoading } = useGetPrivacyRequestsQuery(
    location ? { location } : undefined,
    { refetchOnMountOrArgChange: true },
  );

  // Pivot the backend's action-type-keyed response into a bucket-keyed
  // structure, computed once per fetch.
  const countsByBucket = useMemo(() => pivotSlaHealthByBucket(data), [data]);

  if (!heliosInsights) {
    return null;
  }

  return (
    <Flex
      className={classNames("w-full")}
      gap="middle"
      data-testid="request-insights"
    >
      {SLA_BUCKET_ORDER.map((bucket, idx) => (
        <Fragment key={bucket}>
          {idx > 0 && <Divider vertical className="h-full" />}
          <RequestProgressWidget
            bucket={bucket}
            counts={countsByBucket[bucket]}
            lastUpdated={data?.last_updated ?? undefined}
            isLoading={isLoading}
          />
        </Fragment>
      ))}
    </Flex>
  );
};

export default RequestInsights;
