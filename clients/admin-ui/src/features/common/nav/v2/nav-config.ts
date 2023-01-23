export type NavConfigRoute = {
  dataTestId?: string;
  exact?: boolean;
  path: string;
  requiresPlus?: boolean;
  title?: string;
};

export type NavConfigGroup = {
  dataTestId?: string;
  requiresConnections?: boolean;
  requiresSystems?: boolean;
  routes: NavConfigRoute[];
  title: string;
};

export const NAV_CONFIG: NavConfigGroup[] = [
  // Goes last because its root path will match everything.
  {
    dataTestId: "nav-link-home",
    title: "Home",
    routes: [
      {
        path: "/",
        exact: true,
      },
    ],
  },
  {
    dataTestId: "nav-link-privacy-requests",
    title: "Privacy requests",
    requiresConnections: true,
    routes: [
      {
        dataTestId: "nav-link-request-manager",
        title: "Request manager",
        path: "/privacy-requests",
      },
      {
        dataTestId: "nav-link-connection-manager",
        title: "Connection manager",
        path: "/datastore-connection",
      },
    ],
  },
  {
    dataTestId: "nav-link-data-map",
    title: "Data map",
    requiresSystems: true,
    routes: [
      {
        dataTestId: "nav-link-view-map",
        title: "View map",
        path: "/datamap",
        requiresPlus: true,
      },
      {
        dataTestId: "nav-link-view-systems",
        title: "View systems",
        path: "/system",
      },
      {
        dataTestId: "nav-link-add-systems",
        title: "Add systems",
        path: "/add-systems",
      },
      {
        dataTestId: "nav-link-manage-datasets",
        title: "Manage datasets",
        path: "/dataset",
      },
      {
        dataTestId: "nav-link-classify-systems",
        title: "Classify systems",
        path: "/classify-systems",
        requiresPlus: true,
      },
    ],
  },
  {
    dataTestId: "nav-link-management",
    title: "Management",
    routes: [
      { dataTestId: "nav-link-taxonomy", title: "Taxonomy", path: "/taxonomy" },
      {
        dataTestId: "nav-link-users",
        title: "Users",
        path: "/user-management",
      },
      {
        dataTestId: "nav-link-about-fides",
        title: "About Fides",
        path: "/management/about",
      },
    ],
  },
];

export type NavGroupChild = {
  dataTestId?: string;
  exact?: boolean;
  path: string;
  title: string;
};

export type NavGroup = {
  /**
   * The routes that are nested under this group. These are displayed in the NavSideBar. If this has
   * only one child, the side bar should not be shown at all (such as for "Home").
   */
  children: Array<NavGroupChild>;
  /**
   * Attribute used to identify a DOM node for testing purposes
   */
  dataTestId?: string;
  /**
   * Title of the group. Displayed in NavTopBar.
   */
  title: string;
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
      dataTestId: group.dataTestId,
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
        dataTestId: route.dataTestId,
        exact: route.exact,
        path: route.path,
        title: route.title ?? navGroup.title,
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
