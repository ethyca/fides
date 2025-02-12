import { Icons } from "fidesui";

import { FlagNames } from "~/features/common/features";
import { ScopeRegistryEnum } from "~/types/api";

import * as routes from "./routes";

export type NavConfigRoute = {
  title?: string;
  path: string;
  exact?: boolean;
  requiresPlus?: boolean;
  requiresOss?: boolean;
  requiresFlag?: FlagNames;
  requiresFidesCloud?: boolean;
  /** This route is only available if the user has ANY of these scopes */
  scopes: ScopeRegistryEnum[];
  /** Child routes which will be rendered in the side nav */
  routes?: NavConfigRoute[];
};

export type NavConfigGroup = {
  title: string;
  icon: React.ReactNode;
  routes: NavConfigRoute[];
};

export const NAV_CONFIG: NavConfigGroup[] = [
  {
    icon: <Icons.Home />,
    title: "Overview",
    routes: [
      {
        title: "Home",
        path: "/",
        exact: true,
        scopes: [],
      },
    ],
  },
  {
    title: "Detection & Discovery",
    icon: <Icons.DataAnalytics />,
    routes: [
      {
        title: "Action center",
        path: routes.ACTION_CENTER_ROUTE,
        scopes: [],
        requiresFlag: "webMonitor",
        requiresPlus: true,
      },
      {
        title: "Activity",
        path: routes.DETECTION_DISCOVERY_ACTIVITY_ROUTE,
        scopes: [],
        requiresFlag: "dataDiscoveryAndDetection",
        requiresPlus: true,
      },
      {
        title: "Data detection",
        path: routes.DATA_DETECTION_ROUTE,
        scopes: [],
        requiresFlag: "dataDiscoveryAndDetection",
        requiresPlus: true,
      },
      {
        title: "Data discovery",
        path: routes.DATA_DISCOVERY_ROUTE,
        scopes: [],
        requiresFlag: "dataDiscoveryAndDetection",
        requiresPlus: true,
      },
      {
        title: "Data catalog",
        path: routes.DATA_CATALOG_ROUTE,
        scopes: [],
        requiresFlag: "dataCatalog",
        requiresPlus: true,
      },
    ],
  },
  {
    title: "Data inventory",
    icon: <Icons.DataTable />,
    routes: [
      {
        title: "Data lineage",
        path: routes.DATAMAP_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.DATAMAP_READ],
      },
      {
        title: "System inventory",
        path: routes.SYSTEM_ROUTE,
        scopes: [ScopeRegistryEnum.SYSTEM_READ],
      },
      {
        title: "Add systems",
        path: routes.ADD_SYSTEMS_ROUTE,
        scopes: [ScopeRegistryEnum.SYSTEM_CREATE],
      },
      {
        title: "Manage datasets",
        path: routes.DATASET_ROUTE,
        scopes: [
          ScopeRegistryEnum.CTL_DATASET_CREATE,
          ScopeRegistryEnum.CTL_DATASET_UPDATE,
        ],
      },
      {
        title: "Reporting",
        path: routes.REPORTING_DATAMAP_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.DATAMAP_READ],
      },
    ],
  },
  {
    title: "Privacy requests",
    icon: <Icons.MessageQueue />,
    routes: [
      {
        title: "Request manager",
        path: routes.PRIVACY_REQUESTS_ROUTE,
        scopes: [
          ScopeRegistryEnum.PRIVACY_REQUEST_READ,
          ScopeRegistryEnum.PRIVACY_REQUEST_CREATE,
        ],
      },
      {
        title: "Connection manager",
        path: routes.DATASTORE_CONNECTION_ROUTE,
        scopes: [ScopeRegistryEnum.CONNECTION_CREATE_OR_UPDATE],
      },
      {
        title: "Configuration",
        path: routes.PRIVACY_REQUESTS_CONFIGURATION_ROUTE,
        requiresFlag: "privacyRequestsConfiguration",
        scopes: [ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE],
      },
    ],
  },
  {
    title: "Consent",
    icon: <Icons.SettingsAdjust />,
    routes: [
      {
        title: "Vendors",
        path: routes.CONFIGURE_CONSENT_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PRIVACY_NOTICE_READ],
      },
      {
        title: "Notices",
        path: routes.PRIVACY_NOTICES_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PRIVACY_NOTICE_READ],
      },
      {
        title: "Experiences",
        path: routes.PRIVACY_EXPERIENCE_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PRIVACY_EXPERIENCE_READ],
      },
      {
        title: "Consent reporting",
        path: routes.CONSENT_REPORTING_ROUTE,
        requiresFlag: "consentReporting",
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PRIVACY_NOTICE_READ],
      },
    ],
  },
  {
    title: "Settings",
    icon: <Icons.Settings />,
    routes: [
      {
        title: "Properties",
        path: routes.PROPERTIES_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PROPERTY_READ],
      },
      {
        title: "Messaging",
        path: routes.MESSAGING_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.MESSAGING_TEMPLATE_UPDATE],
      },
      {
        title: "Users",
        path: routes.USER_MANAGEMENT_ROUTE,
        scopes: [
          ScopeRegistryEnum.USER_UPDATE,
          ScopeRegistryEnum.USER_CREATE,
          ScopeRegistryEnum.USER_PERMISSION_UPDATE,
          ScopeRegistryEnum.USER_READ,
        ],
      },
      {
        title: "Integrations",
        path: routes.INTEGRATION_MANAGEMENT_ROUTE,
        requiresFlag: "dataDiscoveryAndDetection",
        requiresPlus: true,
        scopes: [
          ScopeRegistryEnum.CONNECTION_AUTHORIZE,
          ScopeRegistryEnum.CONNECTION_CREATE_OR_UPDATE,
          ScopeRegistryEnum.CONNECTION_DELETE,
          ScopeRegistryEnum.CONNECTION_INSTANTIATE,
          ScopeRegistryEnum.CONNECTION_READ,
          ScopeRegistryEnum.CONNECTION_TYPE_READ,
        ],
      },
      {
        title: "Organization",
        path: routes.ORGANIZATION_MANAGEMENT_ROUTE,
        requiresFlag: "organizationManagement",
        scopes: [
          ScopeRegistryEnum.ORGANIZATION_READ,
          ScopeRegistryEnum.ORGANIZATION_UPDATE,
        ],
      },
      {
        title: "Locations",
        path: routes.LOCATIONS_ROUTE,
        scopes: [
          ScopeRegistryEnum.LOCATION_READ,
          ScopeRegistryEnum.LOCATION_UPDATE,
        ],
        requiresPlus: true,
      },
      {
        title: "Regulations",
        path: routes.REGULATIONS_ROUTE,
        scopes: [
          ScopeRegistryEnum.LOCATION_READ,
          ScopeRegistryEnum.LOCATION_UPDATE,
        ],
        requiresPlus: true,
      },
      {
        title: "Taxonomy",
        path: routes.TAXONOMY_ROUTE,
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
        title: "Custom fields",
        path: routes.CUSTOM_FIELDS_ROUTE,
        scopes: [ScopeRegistryEnum.CUSTOM_FIELD_READ],
        requiresPlus: true,
      },
      {
        title: "Email templates",
        path: routes.EMAIL_TEMPLATES_ROUTE,
        requiresOss: true,
        scopes: [ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE],
      },
      {
        title: "Domain verification",
        path: routes.DOMAIN_RECORDS_ROUTE,
        requiresPlus: true,
        requiresFidesCloud: true,
        scopes: [ScopeRegistryEnum.FIDES_CLOUD_CONFIG_READ],
      },
      {
        title: "Domains",
        path: routes.DOMAIN_MANAGEMENT_ROUTE,
        requiresPlus: true,
        requiresFidesCloud: false,
        scopes: [
          ScopeRegistryEnum.CONFIG_READ,
          ScopeRegistryEnum.CONFIG_UPDATE,
        ],
      },
      {
        title: "Consent",
        path: routes.GLOBAL_CONSENT_CONFIG_ROUTE,
        requiresPlus: true,
        requiresFidesCloud: false,
        scopes: [
          ScopeRegistryEnum.TCF_PUBLISHER_OVERRIDE_READ,
          ScopeRegistryEnum.TCF_PUBLISHER_OVERRIDE_UPDATE,
        ],
      },
      {
        title: "About Fides",
        path: routes.ABOUT_ROUTE,
        scopes: [ScopeRegistryEnum.USER_READ], // temporary scope while we don't have a scope for beta features
      },
    ],
  },
];

if (process.env.NEXT_PUBLIC_APP_ENV === "development") {
  NAV_CONFIG.push({
    title: "Developer",
    icon: <Icons.Code />,
    routes: [
      {
        title: "Ant Design POC",
        path: routes.ANT_POC_ROUTE,
        scopes: [],
      },
    ],
  });
}

export type NavGroupChild = {
  title: string;
  path: string;
  exact?: boolean;
  children: Array<NavGroupChild>;
};

export type NavGroup = {
  /**
   * Title of the group. Displayed as an accordion in MainSideNav.
   */
  title: string;
  /**
   * The routes that are nested under this group. These are displayed inside of each group's accordion.
   */
  children: Array<NavGroupChild>;

  /**
   * Icon to display in the accordion header
   */
  icon: React.ReactNode;
};

/** If all routes in the group require plus and plus is not running then return true */
const navAllGroupReqsPlus = (group: NavConfigGroup, hasPlus: boolean) => {
  if (group.routes.every((route) => route.requiresPlus) && !hasPlus) {
    return true;
  }
  return false;
};
/**
 * If a group contains only routes that the user cannot access, return false.
 * An empty list of scopes is a special case where any scope works.
 */
const navGroupInScope = (
  group: NavConfigGroup,
  userScopes: ScopeRegistryEnum[],
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
  userScopes: ScopeRegistryEnum[],
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

interface ConfigureNavProps {
  config: NavConfigGroup[];
  userScopes: ScopeRegistryEnum[];
  hasPlus?: boolean;
  hasFidesCloud?: boolean;
  flags?: Record<string, boolean>;
}

const configureNavRoute = ({
  route,
  hasPlus,
  flags,
  userScopes,
  hasFidesCloud,
  navGroupTitle,
}: Omit<ConfigureNavProps, "config"> & {
  route: NavConfigRoute;
  navGroupTitle: string;
}): NavGroupChild | undefined => {
  // If the target route would require plus in a non-plus environment,
  // exclude it from the group.
  if (route.requiresPlus && !hasPlus) {
    return undefined;
  }

  // If the target route would require Oss in a Plus environment,
  // exclude it from the group.
  if (route.requiresOss && hasPlus) {
    return undefined;
  }

  // If the target route would require fides cloud in a non-fides-cloud environment,
  // exclude it from the group.
  if (route.requiresFidesCloud && !hasFidesCloud) {
    return undefined;
  }

  // If the target route is protected by a feature flag that is not enabled,
  // exclude it from the group
  if (route.requiresFlag && (!flags || !flags[route.requiresFlag])) {
    return undefined;
  }

  // If the target route is protected by a scope that the user does not
  // have, exclude it from the group
  if (!navRouteInScope(route, userScopes)) {
    return undefined;
  }

  const children: NavGroupChild["children"] = [];
  if (route.routes) {
    route.routes.forEach((childRoute) => {
      const configuredChildRoute = configureNavRoute({
        route: childRoute,
        userScopes,
        hasPlus,
        flags,
        hasFidesCloud,
        navGroupTitle,
      });
      if (configuredChildRoute) {
        children.push(configuredChildRoute);
      }
    });
  }

  const groupChild: NavGroupChild = {
    title: route.title ?? navGroupTitle,
    path: route.path,
    exact: route.exact,
    children,
  };

  return groupChild;
};

export const configureNavGroups = ({
  config,
  userScopes,
  hasPlus = false,
  hasFidesCloud = false,
  flags,
}: ConfigureNavProps): NavGroup[] => {
  const navGroups: NavGroup[] = [];
  config.forEach((group) => {
    // if no nav routes are scoped for the user or all require plus
    if (
      !navGroupInScope(group, userScopes) ||
      navAllGroupReqsPlus(group, hasPlus)
    ) {
      return;
    }

    const navGroup: NavGroup = {
      title: group.title,
      icon: group.icon,
      children: [],
    };

    group.routes.forEach((route) => {
      const routeConfig = configureNavRoute({
        route,
        hasPlus,
        flags,
        userScopes,
        hasFidesCloud,
        navGroupTitle: group.title,
      });
      if (routeConfig) {
        navGroup.children.push(routeConfig);
      }
    });

    // Add navgroup if it has routes available
    if (navGroup.children.length) {
      navGroups.push(navGroup);
    }
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
      child.exact ? path === child.path : path.startsWith(child.path),
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
