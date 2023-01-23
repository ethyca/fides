export type NavConfigRoute = {
  title?: string;
  path: string;
  exact?: boolean;
  requiresPlus?: boolean;
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
      },
    ],
  },
  {
    title: "Privacy requests",
    requiresConnections: true,
    routes: [
      { title: "Request manager", path: "/privacy-requests" },
      { title: "Connection manager", path: "/datastore-connection" },
      { title: "Configuration", path: "/privacy-requests/configure" },
    ],
  },
  {
    title: "Data map",
    requiresSystems: true,
    routes: [
      { title: "View map", path: "/datamap", requiresPlus: true },
      { title: "View systems", path: "/system" },
      { title: "Add systems", path: "/add-systems" },
      { title: "Manage datasets", path: "/dataset" },
      {
        title: "Classify systems",
        path: "/classify-systems",
        requiresPlus: true,
      },
    ],
  },
  {
    title: "Management",
    routes: [
      { title: "Taxonomy", path: "/taxonomy" },
      { title: "Users", path: "/user-management" },
      { title: "About Fides", path: "/management/about" },
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
  hasPlus = false,
  hasSystems = false,
  hasConnections = false,
}: {
  config: NavConfigGroup[];
  hasPlus?: boolean;
  hasSystems?: boolean;
  hasConnections?: boolean;
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
