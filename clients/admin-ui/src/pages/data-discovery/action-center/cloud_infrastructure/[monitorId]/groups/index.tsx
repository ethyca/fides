import { NextPage } from "next";
import { useParams } from "next/navigation";

import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { CloudInfraGroupsTable } from "~/features/data-discovery-and-detection/action-center/tables/CloudInfraGroupsTable";

import { MONITOR_CLOUD_INFRASTRUCTURE_ACTION_CENTER_CONFIG } from "..";

const CloudInfrastructureMonitorGroups: NextPage = () => {
  const params = useParams<{ monitorId: string }>();

  const monitorId = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorId;

  return (
    <ActionCenterLayout
      monitorId={monitorId}
      routeConfig={MONITOR_CLOUD_INFRASTRUCTURE_ACTION_CENTER_CONFIG}
    >
      {loading ? null : <CloudInfraGroupsTable monitorId={monitorId} />}
    </ActionCenterLayout>
  );
};

export default CloudInfrastructureMonitorGroups;
