import { NextPage } from "next";
import { useParams } from "next/navigation";

import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";

import { MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG } from "..";

const InfrastructureMonitorActivity: NextPage = () => {
  const params = useParams<{ monitorId: string }>();

  const monitorId = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorId;

  return (
    <ActionCenterLayout
      monitorId={monitorId}
      routeConfig={MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG}
    >
      {loading ? null : <InProgressMonitorTasksList filters={{ monitorId }} />}
    </ActionCenterLayout>
  );
};

export default InfrastructureMonitorActivity;
