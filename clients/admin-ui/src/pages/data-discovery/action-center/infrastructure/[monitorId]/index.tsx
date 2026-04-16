import { NextPage } from "next";
import { useParams } from "next/navigation";
import { useDispatch } from "react-redux";

import ErrorPage from "~/features/common/errors/ErrorPage";
import {
  ACTION_CENTER_INFRASTRUCTURE_MONITOR_ACTIVITY_ROUTE,
  ACTION_CENTER_INFRASTRUCTURE_MONITOR_ROUTE,
} from "~/features/common/nav/routes";
import { useCalcAggregateStatisticsMutation } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import { useDiscoveredInfrastructureSystemsTable } from "~/features/data-discovery-and-detection/action-center/hooks/useDiscoveredInfrastructureSystemsTable";
import { DiscoveredInfrastructureSystemsTable } from "~/features/data-discovery-and-detection/action-center/tables/DiscoveredInfrastructureSystemsTable";
import { discoveryDetectionUtil } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

export const MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]:
    ACTION_CENTER_INFRASTRUCTURE_MONITOR_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]:
    ACTION_CENTER_INFRASTRUCTURE_MONITOR_ROUTE,
} as const;

const InfrastructureMonitorResultSystems: NextPage = () => {
  const params = useParams<{ monitorId: string }>();
  const dispatch = useDispatch();

  const [trigger] = useCalcAggregateStatisticsMutation();
  const monitorId = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorId;
  const { error: infrastructureSystemsError } =
    useDiscoveredInfrastructureSystemsTable({
      monitorId,
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
      monitorType={APIMonitorType.INFRASTRUCTURE}
      routeConfig={MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG}
      refresh={async () => {
        dispatch(
          discoveryDetectionUtil.invalidateTags([
            "Discovery Monitor Results",
            "Identity Provider Monitor Results",
          ]),
        );
        await trigger({
          monitor_config_id: monitorId,
          monitor_type: APIMonitorType.INFRASTRUCTURE,
        });
      }}
    >
      {loading ? null : (
        <DiscoveredInfrastructureSystemsTable monitorId={monitorId} />
      )}
    </ActionCenterLayout>
  );
};

export default InfrastructureMonitorResultSystems;
