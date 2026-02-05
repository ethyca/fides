import { Result } from "fidesui";
import { NextPage } from "next";
import { useParams } from "next/navigation";

import { useFeatures } from "~/features/common/features";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";

import {
  HELIOS_ACCESS_ERROR,
  MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG,
} from "..";

const InfrastructureMonitorActivity: NextPage = () => {
  const {
    flags: { heliosV2 },
  } = useFeatures();
  const params = useParams<{ monitorId: string }>();

  const monitorKey = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorKey;
  const error = !heliosV2 && HELIOS_ACCESS_ERROR;

  if (error) {
    return <Result status="error" title={error} />;
  }

  return (
    <ActionCenterLayout
      monitorId={monitorKey}
      routeConfig={MONITOR_INFRASTRUCTURE_ACTION_CENTER_CONFIG}
    >
      {loading ? null : <InProgressMonitorTasksList filters={{ monitorKey }} />}
    </ActionCenterLayout>
  );
};

export default InfrastructureMonitorActivity;
