import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  configureNavGroups,
  findActiveNav,
  NAV_CONFIG,
} from "~/features/common/nav/nav-config";
import { selectThisUsersScopes } from "~/features/user-management";

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
        userScopes,
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
