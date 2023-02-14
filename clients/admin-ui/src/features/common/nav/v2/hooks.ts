import { useMemo } from "react";

import { useFeatures } from "~/features/common/features";

import { configureNavGroups, findActiveNav, NAV_CONFIG } from "./nav-config";

export const useNav = ({ path }: { path: string }) => {
  const features = useFeatures();

  const navGroups = useMemo(
    () =>
      configureNavGroups({
        config: NAV_CONFIG,
        hasPlus: features.plus,
        hasSystems: features.systemsCount > 0,
        hasConnections: features.connectionsCount > 0,
        hasAccessToPrivacyRequestConfigurations:
          features.flags.privacyRequestsConfiguration,
      }),
    [features]
  );

  const activeNav = useMemo(
    () => findActiveNav({ navGroups, path }),
    [path, navGroups]
  );

  const nav = useMemo(
    () => ({ groups: navGroups, active: activeNav }),
    [navGroups, activeNav]
  );

  return nav;
};
