import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  configureNavGroups,
  findActiveNav,
  NAV_CONFIG,
} from "~/features/common/nav/nav-config";
import { selectThisUsersScopes } from "~/features/user-management";
import { ScopeRegistryEnum } from "~/types/api";

/** When true in dev, nav shows all items regardless of user scopes (nav only). */
const devShowPlusNav =
  process.env.NODE_ENV === "development" &&
  process.env.NEXT_PUBLIC_DEV_SHOW_PLUS_NAV === "true";

const ALL_SCOPES = Object.values(ScopeRegistryEnum);

export const useNav = ({ path }: { path: string }) => {
  const features = useFeatures();
  const userScopes = useAppSelector(selectThisUsersScopes);

  const navGroups = useMemo(
    () =>
      configureNavGroups({
        config: NAV_CONFIG,
        hasPlus: features.plus,
        flags: features.flags,
        hasFidesCloud: features.fidesCloud,
        userScopes: devShowPlusNav ? ALL_SCOPES : userScopes,
      }),
    [features, userScopes],
  );

  const activeNav = useMemo(
    () => findActiveNav({ navGroups, path }),
    [path, navGroups],
  );

  const nav = useMemo(
    () => ({ groups: navGroups, active: activeNav }),
    [navGroups, activeNav],
  );

  return nav;
};
