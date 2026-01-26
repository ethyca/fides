import { Result } from "fidesui";
import { NextPage } from "next";
import { useParams } from "next/navigation";

import { useFeatures } from "~/features/common/features";
import {
  ACTION_CENTER_INFRASTRUCTURE_MONITOR_ACTIVITY_ROUTE,
  ACTION_CENTER_INFRASTRUCTURE_MONITOR_ROUTE,
} from "~/features/common/nav/routes";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import { DiscoveredInfrastructureSystemsTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredInfrastructureSystemsTable";

export const MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]:
    ACTION_CENTER_INFRASTRUCTURE_MONITOR_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]:
    ACTION_CENTER_INFRASTRUCTURE_MONITOR_ROUTE,
} as const;

export const HELIOS_ACCESS_ERROR =
  "Attempting to access monitor results without the required feature flag enabled";

const InfrastructureMonitorResultSystems: NextPage = () => {
  const {
    flags: { heliosV2 },
  } = useFeatures();
  const params = useParams<{ monitorId: string }>();

  const monitorId = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorId;
  const error = !heliosV2 && HELIOS_ACCESS_ERROR;

  if (error) {
    return <Result status="error" title={error} />;
  }

  return (
    <ActionCenterLayout
      monitorId={monitorId}
      routeConfig={MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG}
    >
      {loading ? null : (
        <DiscoveredInfrastructureSystemsTable monitorId={monitorId} />
      )}
    </ActionCenterLayout>
  );
};

export default InfrastructureMonitorResultSystems;
