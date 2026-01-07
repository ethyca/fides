import { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import {
  ACTION_CENTER_ROUTE,
  ACTION_CENTER_WEBSITE_MONITOR_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetDiscoveredSystemAggregateQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { useDiscoveredAssetsTable } from "~/features/data-discovery-and-detection/action-center/hooks/useDiscoveredAssetsTable";
import { DiscoveredAssetsTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredAssetsTable";
import { MONITOR_TYPES } from "~/features/data-discovery-and-detection/action-center/utils/getMonitorType";
import { DiffStatus } from "~/types/api/models/DiffStatus";

const MonitorResultAssets: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const systemId = decodeURIComponent(router.query.systemId as string);

  const { data: systemResults } = useGetDiscoveredSystemAggregateQuery({
    key: monitorId,
    page: 1,
    size: 1,
    search: "",
    diff_status: [DiffStatus.ADDITION],
    resolved_system_id: systemId,
  });
  const system = systemResults?.items[0];

  // if there are no results, redirect to the monitor page
  useEffect(() => {
    if (!!systemResults && systemResults.items.length === 0) {
      router.push({
        pathname: ACTION_CENTER_WEBSITE_MONITOR_ROUTE,
        query: {
          monitorId: encodeURIComponent(monitorId),
        },
      });
    }
  }, [systemResults, router, monitorId]);

  const { error } = useDiscoveredAssetsTable({
    monitorId,
    systemId,
  });

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your assets"
      />
    );
  }

  return (
    <FixedLayout title="Action center - Discovered assets">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          {
            title: monitorId,
            href: `${ACTION_CENTER_ROUTE}/${MONITOR_TYPES.WEBSITE}/${monitorId}`,
          },
          {
            title:
              systemId === UNCATEGORIZED_SEGMENT
                ? "Uncategorized assets"
                : system?.name,
          },
        ]}
        isSticky={false}
      />
      <DiscoveredAssetsTable
        monitorId={monitorId}
        systemId={systemId}
        consentStatus={system?.consent_status}
      />
    </FixedLayout>
  );
};

export default MonitorResultAssets;
