import { ReactNode } from "react";

import { useFeatures } from "~/features/common/features";
import useHashNavigation from "~/features/common/hooks/useHashNavigation";

export enum ActionCenterHash {
  ATTENTION_REQUIRED = "attention-required",
  ACTIVITY = "activity",
}

export const ACTION_CENTER_CONFIG: Record<ActionCenterHash, { label: string }> =
  {
    [ActionCenterHash.ACTIVITY]: {
      label: "Activity",
    },
    [ActionCenterHash.ATTENTION_REQUIRED]: {
      label: "Attention required",
    },
  } as const;

export type ActionCenterHashRouteConfig = Record<ActionCenterHash, ReactNode>;

const useActionCenterHashNavigation = (
  routes: Record<ActionCenterHash, ReactNode>,
) => {
  const {
    flags: { heliosV2 },
  } = useFeatures();

  const tabs = {
    [ActionCenterHash.ATTENTION_REQUIRED]:
      ACTION_CENTER_CONFIG["attention-required"],
    ...(heliosV2
      ? { [ActionCenterHash.ACTIVITY]: ACTION_CENTER_CONFIG.activity }
      : {}),
  } as const;

  const { activeHash, setActiveHash } = useHashNavigation({
    keys: Object.values(ActionCenterHash),
  });

  return {
    activeTab: activeHash,
    setActiveTab: setActiveHash,
    tabs,
    route: routes[activeHash],
  };
};

export default useActionCenterHashNavigation;
