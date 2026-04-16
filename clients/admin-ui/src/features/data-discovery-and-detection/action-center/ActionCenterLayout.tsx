import {
  Badge,
  BadgeProps,
  Button,
  Dropdown,
  DropdownProps,
  Flex,
  Icons,
  Menu,
} from "fidesui";
import _ from "lodash";
import { PropsWithChildren, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import useActionCenterNavigation, {
  ActionCenterRoute,
  ActionCenterRouteConfig,
} from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

import MonitorStats from "./MonitorStats";

export interface ActionCenterLayoutProps {
  monitorId?: string;
  routeConfig: ActionCenterRouteConfig;
  pageSettings?: {
    dropdownProps?: DropdownProps;
    badgeProps?: BadgeProps;
  };
  refresh?: () => Promise<void>;
  monitorType?: APIMonitorType;
}

const ActionCenterLayout = ({
  children,
  monitorId,
  monitorType,
  routeConfig,
  pageSettings,
  refresh,
}: PropsWithChildren<ActionCenterLayoutProps>) => {
  const [refreshing, setRefreshing] = useState(false);
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
        rightContent={
          <Flex gap="small">
            {pageSettings && (
              <Flex>
                <Badge {...pageSettings.badgeProps}>
                  <Dropdown {...pageSettings.dropdownProps}>
                    <Button
                      aria-label="Page settings"
                      icon={<Icons.SettingsView />}
                    />
                  </Dropdown>
                </Badge>
              </Flex>
            )}
            {refresh && (
              <Button
                aria-label="Page refresh"
                icon={<Icons.Renew />}
                onClick={async () => {
                  setRefreshing(true);
                  try {
                    await refresh();
                  } finally {
                    setRefreshing(false);
                  }
                }}
                disabled={refreshing}
                loading={refreshing}
              />
            )}
          </Flex>
        }
      />
      {monitorId && monitorType && (
        <MonitorStats monitorId={monitorId} monitorType={monitorType} />
      )}
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
