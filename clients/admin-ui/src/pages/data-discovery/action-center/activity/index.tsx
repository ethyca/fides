import { NextPage } from "next";

import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";

import { ROOT_ACTION_CENTER_CONFIG } from "..";

const ActionCenterActivityPage: NextPage = () => {
  return (
    <ActionCenterLayout routeConfig={ROOT_ACTION_CENTER_CONFIG}>
      <InProgressMonitorTasksList />
    </ActionCenterLayout>
  );
};

export default ActionCenterActivityPage;
