import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { useFeatures } from "~/features/common/features";
import { useGetUserPermissionsQuery } from "~/features/user-management";
import { ScopeRegistry } from "~/types/api";

import { configureNavGroups, findActiveNav, NAV_CONFIG } from "./nav-config";

export const useNav = ({ path }: { path: string }) => {
  const features = useFeatures();
  const user = useAppSelector(selectUser);
  const { data: permissions } = useGetUserPermissionsQuery(user?.id ?? "");

  const navGroups = useMemo(() => {
    // Backend UserPermissions model doesn't automatically type to the same enum
    const userScopes = permissions
      ? (permissions.scopes as ScopeRegistry[])
      : [];
    return configureNavGroups({
      config: NAV_CONFIG,
      hasPlus: features.plus,
      hasSystems: features.systemsCount > 0,
      hasConnections: features.connectionsCount > 0,
      hasAccessToPrivacyRequestConfigurations:
        features.flags.privacyRequestsConfiguration,
      userScopes,
    });
  }, [features, permissions]);

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
