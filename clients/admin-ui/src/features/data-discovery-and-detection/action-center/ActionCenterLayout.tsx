import {
  Badge,
  BadgeProps,
  Button,
  Dropdown,
  DropdownProps,
  Flex,
  Icons,
  Menu,
  Tooltip,
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

import MonitorStats from "./MonitorStats";

export interface ActionCenterLayoutProps {
  monitorId?: string;
  routeConfig: ActionCenterRouteConfig;
  pageSettings?: {
    dropdownProps?: DropdownProps;
    badgeProps?: BadgeProps;
  };
  onRefresh?: () => void;
}

const ActionCenterLayout = ({
  children,
  monitorId,
  routeConfig,
  pageSettings,
  onRefresh,
}: PropsWithChildren<ActionCenterLayoutProps>) => {
  const [statsExpanded, setStatsExpanded] = useState(false);
  const {
    items: menuItems,
    activeItem,
    setActiveItem,
  } = useActionCenterNavigation(routeConfig);

  const tabs = (
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
  );

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
          (pageSettings || onRefresh) && (
            <Flex gap="small">
              {pageSettings && (
                <Badge {...pageSettings.badgeProps}>
                  <Dropdown {...pageSettings.dropdownProps}>
                    <Button
                      aria-label="Page settings"
                      icon={<Icons.SettingsView />}
                    />
                  </Dropdown>
                </Badge>
              )}
              {onRefresh && (
                <Tooltip title="Refresh">
                  <Button
                    icon={<Icons.Renew />}
                    onClick={onRefresh}
                    aria-label="Refresh"
                  />
                </Tooltip>
              )}
            </Flex>
          )
        }
      />
      {monitorId ? (
        // Schema explorer: collapsible slim dashboard above content
        <>
          <MonitorStats
            monitorId={monitorId}
            isExpanded={statsExpanded}
            onToggle={() => setStatsExpanded(!statsExpanded)}
          />
          {tabs}
          {children}
        </>
      ) : (
        // Root page: sidebar dashboard next to content
        <Flex className="flex-1 overflow-hidden" gap={0}>
          <div className="flex-none border-r border-solid border-gray-200 pr-3">
            <MonitorStats />
          </div>
          <Flex vertical className="flex-1 overflow-hidden pl-4">
            {tabs}
            {children}
          </Flex>
        </Flex>
      )}
    </FixedLayout>
  );
};

export default ActionCenterLayout;
