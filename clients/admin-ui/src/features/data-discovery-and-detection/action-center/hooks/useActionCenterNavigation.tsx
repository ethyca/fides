import { Icons, MenuProps } from "fidesui";

import { useFeatures } from "~/features/common/features";
import useMenuNavigation from "~/features/common/hooks/useMenuNavigation";

export enum ActionCenterRoute {
  ATTENTION_REQUIRED = "attention-required",
  ACTIVITY = "activity",
}

export const ACTION_CENTER_CONFIG: Record<
  ActionCenterRoute,
  NonNullable<MenuProps["items"]>[number]
> = {
  [ActionCenterRoute.ACTIVITY]: {
    key: ActionCenterRoute.ACTIVITY,
    type: "item",
    label: "Activity",
    icon: <Icons.Activity />,
  },
  [ActionCenterRoute.ATTENTION_REQUIRED]: {
    key: ActionCenterRoute.ATTENTION_REQUIRED,
    type: "item",
    label: "Attention required",
    icon: <Icons.ListBoxes />,
  },
} as const;

export type ActionCenterRouteConfig = Record<ActionCenterRoute, string>;

const useActionCenterNavigation = (routeConfig: ActionCenterRouteConfig) => {
  const {
    flags: { heliosV2 },
  } = useFeatures();

  const items = {
    [ActionCenterRoute.ATTENTION_REQUIRED]:
      ACTION_CENTER_CONFIG["attention-required"],
    ...(heliosV2
      ? { [ActionCenterRoute.ACTIVITY]: ACTION_CENTER_CONFIG.activity }
      : {}),
  } as const;

  const { activeItem, setActiveItem } = useMenuNavigation({
    routes: routeConfig,
    defaultKey: ActionCenterRoute.ATTENTION_REQUIRED,
  });

  return {
    activeItem,
    setActiveItem,
    items,
  };
};

export default useActionCenterNavigation;
