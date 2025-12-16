import { NextPage } from "next";

import {
  ACTION_CENTER_ACTIVITY_ROUTE,
  ACTION_CENTER_ROUTE,
} from "~/features/common/nav/routes";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import MonitorList from "~/features/data-discovery-and-detection/action-center/MonitorList";

export const ROOT_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]: ACTION_CENTER_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]: ACTION_CENTER_ROUTE,
};

const ActionCenterPage: NextPage = () => {
  return (
    <ActionCenterLayout routeConfig={ROOT_ACTION_CENTER_CONFIG}>
      <MonitorList />
    </ActionCenterLayout>
  );
};

export default ActionCenterPage;
