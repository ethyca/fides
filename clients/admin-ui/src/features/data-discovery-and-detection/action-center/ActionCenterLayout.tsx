import { AntMenu as Menu } from "fidesui";
import { PropsWithChildren } from "react";

import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { DisabledMonitorsPage } from "~/features/data-discovery-and-detection/action-center/DisabledMonitorsPage";
import useActionCenterHashNavigation, {
  ActionCenterHash,
  ActionCenterHashRouteConfig,
} from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterHashNavigation";

interface ActionCenterLayoutProps {
  hashRoutes: ActionCenterHashRouteConfig;
  monitor?: string;
}
const ActionCenterLayout = ({
  children,
  hashRoutes,
  monitor,
}: PropsWithChildren<ActionCenterLayoutProps>) => {
  const { tabs, activeTab, setActiveTab, route } =
    useActionCenterHashNavigation(hashRoutes);
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
          ...(monitor ? [{ title: monitor }] : []),
        ]}
        isSticky={false}
      />
      <Menu
        aria-label="Action center tabs"
        mode="horizontal"
        items={Object.entries(tabs).map(([key, { label }]) => ({
          key,
          label,
        }))}
        selectedKeys={[activeTab]}
        onClick={async (menuInfo) => {
          const validKey = Object.values(ActionCenterHash).find(
            (value) => value === menuInfo.key,
          );
          if (validKey) {
            await setActiveTab(validKey);
          }
        }}
        className="mb-4"
        data-testid="action-center-tabs"
      />
      {route}
      {children}
    </FixedLayout>
  );
};

export default ActionCenterLayout;
