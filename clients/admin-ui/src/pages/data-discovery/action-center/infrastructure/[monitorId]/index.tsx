import { NextPage } from "next";
import { useParams, useSearchParams } from "next/navigation";

import ErrorPage from "~/features/common/errors/ErrorPage";
import {
  ACTION_CENTER_INFRASTRUCTURE_MONITOR_ACTIVITY_ROUTE,
  ACTION_CENTER_INFRASTRUCTURE_MONITOR_ROUTE,
} from "~/features/common/nav/routes";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import { useDiscoveredInfrastructureSystemsTable } from "~/features/data-discovery-and-detection/action-center/hooks/useDiscoveredInfrastructureSystemsTable";
import { DiscoveredInfrastructureSystemsTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredInfrastructureSystemsTable";
import { ConnectionType } from "~/types/api";

export const MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]:
    ACTION_CENTER_INFRASTRUCTURE_MONITOR_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]:
    ACTION_CENTER_INFRASTRUCTURE_MONITOR_ROUTE,
} as const;

const InfrastructureMonitorResultSystems: NextPage = () => {
  const params = useParams<{ monitorId: string }>();
  const searchParams = useSearchParams();

  const monitorId = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;

  const isAWSMonitor =
    searchParams?.get("connectionType") === ConnectionType.AWS;
  const loading = !monitorId;

  const { error: infrastructureSystemsError } =
    useDiscoveredInfrastructureSystemsTable({
      monitorId,
      isAWSMonitor,
    });

  if (infrastructureSystemsError) {
    return (
      <ErrorPage
        error={infrastructureSystemsError}
        defaultMessage="A problem occurred while fetching your systems"
      />
    );
  }

  return (
    <ActionCenterLayout
      monitorId={monitorId}
      routeConfig={MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG}
    >
      {loading ? null : (
        <DiscoveredInfrastructureSystemsTable
          monitorId={monitorId}
          isAWSMonitor={isAWSMonitor}
        />
      )}
    </ActionCenterLayout>
  );
};

export default InfrastructureMonitorResultSystems;
