import {
  Badge,
  BadgeProps,
  Button,
  Dropdown,
  DropdownProps,
  Icons,
} from "fidesui";
import { PropsWithChildren } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
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
  searchProps?: {
    value: string;
    onSearch: (value: string) => void;
    placeholder?: string;
  };
}

const ActionCenterLayout = ({
  children,
  monitorId,
  routeConfig,
  pageSettings,
  searchProps,
}: PropsWithChildren<ActionCenterLayoutProps>) => {
  const {
    items: menuItems,
    activeItem,
    setActiveItem,
  } = useActionCenterNavigation(routeConfig);

  const navItems = Object.values(menuItems).flatMap((item) => {
    if (!item || !("key" in item) || !("label" in item)) {
      return [];
    }
    return [{ key: item.key as string, label: item.label as string }];
  });

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Action center"
          breadcrumbItems={[
            { title: "All activity", href: ACTION_CENTER_ROUTE },
            ...(monitorId ? [{ title: monitorId }] : []),
          ]}
        />
        <SidePanel.Navigation
          items={navItems}
          activeKey={activeItem ?? ""}
          onSelect={async (key) => {
            const validKey = Object.values(ActionCenterRoute).find(
              (v) => v === key,
            );
            if (validKey) {
              await setActiveItem(validKey);
            }
          }}
        />
        {searchProps && (
          <SidePanel.Search
            onSearch={searchProps.onSearch}
            value={searchProps.value}
            onChange={(e) => searchProps.onSearch(e.target.value)}
            placeholder={searchProps.placeholder}
          />
        )}
        {pageSettings && (
          <SidePanel.Actions>
            <Badge {...pageSettings.badgeProps}>
              <Dropdown {...pageSettings.dropdownProps}>
                <Button
                  aria-label="Page settings"
                  icon={<Icons.SettingsView />}
                />
              </Dropdown>
            </Badge>
          </SidePanel.Actions>
        )}
      </SidePanel>
      <FixedLayout title="Action center" mainProps={{ overflow: "hidden" }} fullHeight>
        <MonitorStats monitorId={monitorId} />
        {children}
      </FixedLayout>
    </>
  );
};

export default ActionCenterLayout;
