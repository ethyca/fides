import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { selectThisUsersScopes } from "~/features/user-management";

import { configureNavGroups, findActiveNav, NAV_CONFIG } from "./nav-config";

export const useNav = ({ path }: { path: string }) => {
  const features = useFeatures();
  const userScopes = useAppSelector(selectThisUsersScopes);

  const navGroups = useMemo(
    () =>
      configureNavGroups({
        config: NAV_CONFIG,
        hasPlus: features.plus,
        hasSystems: features.systemsCount > 0,
        hasConnections: features.connectionsCount > 0,
        hasAccessToPrivacyRequestConfigurations:
          features.flags.privacyRequestsConfiguration,
        userScopes,
      }),
    [features, userScopes]
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
