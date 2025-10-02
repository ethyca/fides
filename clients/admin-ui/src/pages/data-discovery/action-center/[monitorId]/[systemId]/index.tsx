import { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetDiscoveredSystemAggregateQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { DiscoveredAssetsTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredAssetsTable";
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

  return (
    <FixedLayout title="Action center - Discovered assets">
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorId, href: `${ACTION_CENTER_ROUTE}/${monitorId}` },
          {
            title:
              systemId === UNCATEGORIZED_SEGMENT
                ? "Uncategorized assets"
                : system?.name,
          },
        ]}
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
