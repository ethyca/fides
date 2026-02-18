import { Button, Dropdown, DropdownProps, Flex, Icons, Menu } from "fidesui";
import _ from "lodash";
import { PropsWithChildren } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import useActionCenterNavigation, {
  ActionCenterRoute,
  ActionCenterRouteConfig,
} from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";

export interface ActionCenterLayoutProps {
  monitorId?: string;
  routeConfig: ActionCenterRouteConfig;
  pageSettings?: DropdownProps

}

const ActionCenterLayout = ({
  children,
  monitorId,
  routeConfig,
  pageSettings
}: PropsWithChildren<ActionCenterLayoutProps>) => {
  const {
    items: menuItems,
    activeItem,
    setActiveItem,
  } = useActionCenterNavigation(routeConfig);

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
        rightContent={pageSettings && <Flex>
          <Dropdown
            {...pageSettings}
          >
            <Button icon={<Icons.SettingsView />} />
          </Dropdown>
        </Flex>}

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
