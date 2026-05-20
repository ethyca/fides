import { Icons, MenuProps } from "fidesui";

import useMenuNavigation from "~/features/common/hooks/useMenuNavigation";
import type { NavConfigTab } from "~/features/common/nav/nav-config";
import {
  ACTION_CENTER_ACTIVITY_ROUTE,
  ACTION_CENTER_ROUTE,
} from "~/features/common/nav/routes";

export enum ActionCenterRoute {
  ATTENTION_REQUIRED = "attention-required",
  ACTIVITY = "activity",
  GROUPS = "groups",
}

export const ACTION_CENTER_CONFIG: Record<
  ActionCenterRoute,
  NonNullable<MenuProps["items"]>[number]
> = {
  [ActionCenterRoute.ATTENTION_REQUIRED]: {
    key: ActionCenterRoute.ATTENTION_REQUIRED,
    type: "item",
    label: "Attention required",
    icon: <Icons.ListBoxes />,
  },
  [ActionCenterRoute.GROUPS]: {
    key: ActionCenterRoute.GROUPS,
    type: "item",
    label: "Groups",
    icon: <Icons.Grid />,
  },
  [ActionCenterRoute.ACTIVITY]: {
    key: ActionCenterRoute.ACTIVITY,
    type: "item",
    label: "Activity",
    icon: <Icons.Activity />,
  },
} as const;

/** Shared tab definitions used by both the tab bar and nav search. */
export const ACTION_CENTER_TAB_ITEMS: NavConfigTab[] = [
  { title: "Attention required", path: ACTION_CENTER_ROUTE },
  { title: "Activity", path: ACTION_CENTER_ACTIVITY_ROUTE },
];

export type ActionCenterRouteConfig = Partial<
  Record<ActionCenterRoute, string>
> &
  Record<
    ActionCenterRoute.ATTENTION_REQUIRED | ActionCenterRoute.ACTIVITY,
    string
  >;

const useActionCenterNavigation = (routeConfig: ActionCenterRouteConfig) => {
  const { activeItem, setActiveItem } = useMenuNavigation({
    routes: routeConfig as Record<string, string>,
    defaultKey: ActionCenterRoute.ATTENTION_REQUIRED,
  });

  // Only include menu items for routes present in the config
  const items = Object.fromEntries(
    Object.entries(ACTION_CENTER_CONFIG).filter(([key]) => key in routeConfig),
  );

  return {
    activeItem,
    setActiveItem,
    items,
  };
};

export default useActionCenterNavigation;
