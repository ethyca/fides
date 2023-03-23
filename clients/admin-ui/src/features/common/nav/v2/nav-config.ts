import { ScopeRegistryEnum } from "~/types/api";

export type NavConfigRoute = {
  title?: string;
  path: string;
  exact?: boolean;
  requiresPlus?: boolean;
  /** This route is only available if the user has ANY of these scopes */
  scopes: ScopeRegistryEnum[];
};

export type NavConfigGroup = {
  title: string;
  routes: NavConfigRoute[];
};

export const NAV_CONFIG: NavConfigGroup[] = [
  // Goes last because its root path will match everything.
  {
    title: "Home",
    routes: [
      {
        path: "/",
        exact: true,
        scopes: [],
      },
    ],
  },
  {
    title: "Privacy requests",
    routes: [
      {
        title: "Request manager",
        path: "/privacy-requests",
        scopes: [ScopeRegistryEnum.PRIVACY_REQUEST_READ],
      },
      {
        title: "Connection manager",
        path: "/datastore-connection",
        scopes: [ScopeRegistryEnum.CONNECTION_CREATE_OR_UPDATE],
      },
      {
        title: "Configuration",
        path: "/privacy-requests/configure",
        scopes: [ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE],
      },
    ],
  },
  {
    title: "Data map",
    routes: [
      {
        title: "View map",
        path: "/datamap",
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.DATAMAP_READ],
      },
      {
        title: "View systems",
        path: "/system",
        scopes: [ScopeRegistryEnum.SYSTEM_READ],
      },
      {
        title: "Add systems",
        path: "/add-systems",
        scopes: [ScopeRegistryEnum.SYSTEM_CREATE],
      },
      {
        title: "Manage datasets",
        path: "/dataset",
        scopes: [
          ScopeRegistryEnum.CTL_DATASET_CREATE,
          ScopeRegistryEnum.CTL_DATASET_UPDATE,
        ],
      },
      {
        title: "Classify systems",
        path: "/classify-systems",
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.SYSTEM_UPDATE], // temporary scope until we decide what to do here
      },
    ],
  },
  {
    title: "Management",
    routes: [
      {
        title: "Users",
        path: "/user-management",
        scopes: [
          ScopeRegistryEnum.USER_UPDATE,
          ScopeRegistryEnum.USER_CREATE,
          ScopeRegistryEnum.USER_PERMISSION_UPDATE,
        ],
      },
      {
        title: "Organization",
        path: "/management/organization",
        scopes: [
          ScopeRegistryEnum.ORGANIZATION_READ,
          ScopeRegistryEnum.ORGANIZATION_UPDATE,
        ],
      },
      {
        title: "Taxonomy",
        path: "/taxonomy",
        scopes: [
          ScopeRegistryEnum.DATA_CATEGORY_CREATE,
          ScopeRegistryEnum.DATA_CATEGORY_UPDATE,
          ScopeRegistryEnum.DATA_USE_CREATE,
          ScopeRegistryEnum.DATA_USE_UPDATE,
          ScopeRegistryEnum.DATA_SUBJECT_CREATE,
          ScopeRegistryEnum.DATA_SUBJECT_UPDATE,
        ],
      },
      {
        title: "About Fides",
        path: "/management/about",
        scopes: [ScopeRegistryEnum.USER_READ], // temporary scope while we don't have a scope for beta features
      },
    ],
  },
];

export type NavGroupChild = {
  title: string;
  path: string;
  exact?: boolean;
};

export type NavGroup = {
  /**
   * Title of the group. Displayed in NavTopBar.
   */
  title: string;
  /**
   * The routes that are nested under this group. These are displayed in the NavSideBar. If this has
   * only one child, the side bar should not be shown at all (such as for "Home").
   */
  children: Array<NavGroupChild>;
};

/**
 * If a group contains only routes that the user cannot access, return false.
 * An empty list of scopes is a special case where any scope works.
 */
const navGroupInScope = (
  group: NavConfigGroup,
  userScopes: ScopeRegistryEnum[]
) => {
  if (group.routes.filter((route) => route.scopes.length === 0).length === 0) {
    const allScopesAcrossRoutes = group.routes.reduce((acc, route) => {
      const { scopes } = route;
      return [...acc, ...scopes];
    }, [] as ScopeRegistryEnum[]);
    if (
      allScopesAcrossRoutes.length &&
      allScopesAcrossRoutes.filter((scope) => userScopes.includes(scope))
        .length === 0
    ) {
      return false;
    }
  }
  return true;
};

/**
 * If the user does not have any of the scopes listed in the route's requirements,
 * return false. An empty list of scopes is a special case where any scope works.
 */
const navRouteInScope = (
  route: NavConfigRoute,
  userScopes: ScopeRegistryEnum[]
) => {
  if (
    route.scopes.length &&
    route.scopes.filter((requiredScope) => userScopes.includes(requiredScope))
      .length === 0
  ) {
    return false;
  }
  return true;
};

export const configureNavGroups = ({
  config,
  userScopes,
  hasPlus = false,
  hasAccessToPrivacyRequestConfigurations = false,
  hasAccessToOrganizationManagement = false,
}: {
  config: NavConfigGroup[];
  userScopes: ScopeRegistryEnum[];
  hasPlus?: boolean;
  hasAccessToPrivacyRequestConfigurations?: boolean;
  hasAccessToOrganizationManagement?: boolean;
}): NavGroup[] => {
  const navGroups: NavGroup[] = [];

  config.forEach((group) => {
    if (!navGroupInScope(group, userScopes)) {
      return;
    }

    const navGroup: NavGroup = {
      title: group.title,
      children: [],
    };
    navGroups.push(navGroup);

    group.routes.forEach((route) => {
      // If the target route would require plus in a non-plus environment,
      // exclude it from the group.
      if (route.requiresPlus && !hasPlus) {
        return;
      }

      // If the target route is protected by a feature flag that is disabled,
      // exclude it from the group
      if (
        route.path === "/privacy-requests/configure" &&
        !hasAccessToPrivacyRequestConfigurations
      ) {
        return;
      }

      if (
        route.path === "/management/organization" &&
        !hasAccessToOrganizationManagement
      ) {
        return;
      }

      // If the target route is protected by a scope that the user does not
      // have, exclude it from the group
      if (!navRouteInScope(route, userScopes)) {
        return;
      }

      navGroup.children.push({
        title: route.title ?? navGroup.title,
        path: route.path,
        exact: route.exact,
      });
    });
  });

  return navGroups;
};

export type ActiveNav = NavGroup & { path?: string };

export const findActiveNav = ({
  navGroups,
  path,
}: {
  navGroups: NavGroup[];
  path: string;
}): ActiveNav | undefined => {
  let childMatch: NavGroupChild | undefined;
  const groupMatch = navGroups.find((group) => {
    childMatch = group.children.find((child) =>
      child.exact ? path === child.path : path.startsWith(child.path)
    );
    return childMatch;
  });

  if (!(groupMatch && childMatch)) {
    return undefined;
  }

  let activePath: string | undefined;
  if (childMatch.exact && path === childMatch.path) {
    activePath = path;
  } else if (path.startsWith(childMatch.path)) {
    activePath = childMatch.path;
  }
  return {
    ...groupMatch,
    path: activePath,
  };
};

/**
 * Similar to findActiveNav, but using NavConfig instead of a NavGroup
 * This may not be needed once we remove the progressive nav, since then we can
 * just check what navs are available (they would all be restricted by scope)
 */
export const canAccessRoute = ({
  path,
  userScopes,
}: {
  path: string;
  userScopes: ScopeRegistryEnum[];
}) => {
  let childMatch: NavConfigRoute | undefined;
  const groupMatch = NAV_CONFIG.find((group) => {
    childMatch = group.routes.find((child) =>
      child.exact ? path === child.path : path.startsWith(child.path)
    );
    return childMatch;
  });

  if (!(groupMatch && childMatch)) {
    return false;
  }

  // Special case of empty scopes
  if (childMatch.scopes.length === 0) {
    return true;
  }

  const scopeOverlaps = childMatch.scopes.filter((scope) =>
    userScopes.includes(scope)
  );
  return scopeOverlaps.length > 0;
};
