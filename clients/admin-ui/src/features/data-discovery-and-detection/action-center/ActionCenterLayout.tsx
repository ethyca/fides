import { Menu } from "fidesui";
import _ from "lodash";
import { PropsWithChildren } from "react";

import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { DisabledMonitorsPage } from "~/features/data-discovery-and-detection/action-center/DisabledMonitorsPage";
import useActionCenterNavigation, {
  ActionCenterRoute,
  ActionCenterRouteConfig,
} from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";

export interface ActionCenterLayoutProps {
  monitorId?: string;
  routeConfig: ActionCenterRouteConfig;
}

const ActionCenterLayout = ({
  children,
  monitorId,
  routeConfig,
}: PropsWithChildren<ActionCenterLayoutProps>) => {
  const {
    items: menuItems,
    activeItem,
    setActiveItem,
  } = useActionCenterNavigation(routeConfig);
  const {
    flags: { webMonitor: webMonitorEnabled, heliosV2: heliosV2Enabled },
  } = useFeatures();

  if (!webMonitorEnabled && !heliosV2Enabled) {
    return <DisabledMonitorsPage />;
  }

  return (
    <FixedLayout
      title="Action center"
      mainProps={{ overflow: "hidden" }}
      fullHeight
    >
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          ...(monitorId ? [{ title: monitorId }] : []),
        ]}
        isSticky={false}
      />
      <Menu
        aria-label="Action center tabs"
        mode="horizontal"
        items={Object.values(menuItems)}
        selectedKeys={_.compact([activeItem])}
        onClick={async (menuInfo) => {
          const validKey = Object.values(ActionCenterRoute).find(
            (value) => value === menuInfo.key,
          );
          if (validKey) {
            await setActiveItem(validKey);
          }
        }}
        className="mb-4"
        data-testid="action-center-tabs"
      />
      {children}
    </FixedLayout>
  );
};

export default ActionCenterLayout;
