import { NextPage } from "next";

import { useFeatures } from "~/features/common/features";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";
import { DisabledMonitorsPage } from "~/features/data-discovery-and-detection/action-center/DisabledMonitorsPage";
import { ActionCenterHash } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterHashNavigation";
import MonitorList from "~/features/data-discovery-and-detection/action-center/MonitorList";

const ActionCenterPage: NextPage = () => {
  const {
    flags: { webMonitor: webMonitorEnabled, heliosV2: heliosV2Enabled },
  } = useFeatures();

  if (!webMonitorEnabled && !heliosV2Enabled) {
    return <DisabledMonitorsPage />;
  }

  return (
    <ActionCenterLayout
      hashRoutes={{
        [ActionCenterHash.ACTIVITY]: <InProgressMonitorTasksList />,
        [ActionCenterHash.ATTENTION_REQUIRED]: <MonitorList />,
      }}
    />
  );
};

export default ActionCenterPage;
