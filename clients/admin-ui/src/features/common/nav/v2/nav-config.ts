import { ScopeRegistry } from "~/types/api";

export type NavConfigRoute = {
  title?: string;
  path: string;
  exact?: boolean;
  requiresPlus?: boolean;
  /** This route is only available if the user has ANY of these scopes */
  scopes: ScopeRegistry[];
};

export type NavConfigGroup = {
  title: string;
  requiresSystems?: boolean;
  requiresConnections?: boolean;
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
    requiresConnections: true,
    routes: [
      {
        title: "Request manager",
        path: "/privacy-requests",
        scopes: [ScopeRegistry.PRIVACY_REQUEST_READ],
      },
      {
        title: "Connection manager",
        path: "/datastore-connection",
        scopes: [ScopeRegistry.CONNECTION_CREATE_OR_UPDATE],
      },
      {
        title: "Configuration",
        path: "/privacy-requests/configure",
        scopes: [ScopeRegistry.MESSAGING_CREATE_OR_UPDATE],
      },
    ],
  },
  {
    title: "Data map",
    requiresSystems: true,
    routes: [
      {
        title: "View map",
        path: "/datamap",
        requiresPlus: true,
        scopes: [ScopeRegistry.DATAMAP_READ],
      },
      {
        title: "View systems",
        path: "/system",
        scopes: [ScopeRegistry.CLI_OBJECTS_READ],
      },
      {
        title: "Add systems",
        path: "/add-systems",
        scopes: [
          ScopeRegistry.CLI_OBJECTS_CREATE,
          ScopeRegistry.CLI_OBJECTS_UPDATE,
        ],
      },
      {
        title: "Manage datasets",
        path: "/dataset",
        scopes: [
          ScopeRegistry.CLI_OBJECTS_CREATE,
          ScopeRegistry.CLI_OBJECTS_UPDATE,
        ],
      },
      {
        title: "Classify systems",
        path: "/classify-systems",
        requiresPlus: true,
        scopes: [], // this path may be going away soon
      },
    ],
  },
  {
    title: "Management",
    routes: [
      {
        title: "Taxonomy",
        path: "/taxonomy",
        scopes: [ScopeRegistry.CLI_OBJECTS_READ],
      },
      {
        title: "Users",
        path: "/user-management",
        scopes: [ScopeRegistry.USER_READ],
      },
      { title: "About Fides", path: "/management/about", scopes: [] },
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

export const configureNavGroups = ({
  config,
  userScopes,
  hasPlus = false,
  hasSystems = false,
  hasConnections = false,
  hasAccessToPrivacyRequestConfigurations = false,
}: {
  config: NavConfigGroup[];
  userScopes: ScopeRegistry[];
  hasPlus?: boolean;
  hasSystems?: boolean;
  hasConnections?: boolean;
  hasAccessToPrivacyRequestConfigurations?: boolean;
}): NavGroup[] => {
  const navGroups: NavGroup[] = [];

  config.forEach((group) => {
    // Skip groups with unmet requirements.
    if (
      (group.requiresConnections && !hasConnections) ||
      (group.requiresSystems && !hasSystems)
    ) {
      return;
    }

    // Skip groups that contain only routes the user cannot access
    // an empty scopes [] is a special case where everything should succeed
    if (
      group.routes.filter((route) => route.scopes.length === 0).length === 0
    ) {
      const allScopesAcrossRoutes = group.routes.reduce((acc, route) => {
        const { scopes } = route;
        return [...acc, ...scopes];
      }, [] as ScopeRegistry[]);
      if (
        allScopesAcrossRoutes.length &&
        allScopesAcrossRoutes.filter((scope) => userScopes.includes(scope))
          .length === 0
      ) {
        return;
      }
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

      if (
        route.path === "/privacy-requests/configure" &&
        !hasAccessToPrivacyRequestConfigurations
      ) {
        return;
      }

      // If the user does not have any of the scopes listed in the route's requirements,
      // exclude it from the group.
      if (
        route.scopes.length &&
        route.scopes.filter((requiredScope) =>
          userScopes.includes(requiredScope)
        ).length === 0
      ) {
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
