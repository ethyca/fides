import { Icons } from "fidesui";
import { ReactNode } from "react";

import { FlagNames } from "~/features/common/features";
import { NOTIFICATION_TAB_ITEMS } from "~/features/common/NotificationTabs";
import { ACTION_CENTER_TAB_ITEMS } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import { PRIVACY_REQUEST_TAB_ITEMS } from "~/features/privacy-requests/hooks/usePrivacyRequestTabs";
import { ScopeRegistryEnum } from "~/types/api";

import * as routes from "./routes";

export interface NavConfigTab {
  title: string;
  path: string;
}

export interface NavConfigRoute {
  title?: string;
  path: string;
  exact?: boolean;
  requiresPlus?: boolean;
  requiresOss?: boolean;
  requiresFlag?: FlagNames;
  /** Show route if ANY of these flags are enabled (OR logic) */
  requiresAnyFlag?: FlagNames[];
  /** Hide route if this flag is enabled */
  hidesIfFlag?: FlagNames;
  requiresFidesCloud?: boolean;
  /** Hide this route from the navigation UI but still allow access */
  hidden?: boolean;
  /** This route is only available if the user has ANY of these scopes */
  scopes: ScopeRegistryEnum[];
  /** Child routes which will be rendered in the side nav */
  routes?: NavConfigRoute[];
  /** Tabs within this page that should appear in search */
  tabs?: NavConfigTab[];
}

export interface NavConfigGroup {
  title: string;
  icon: ReactNode;
  routes: NavConfigRoute[];
}

export const NAV_CONFIG: NavConfigGroup[] = [
  // 1. Dashboard
  {
    icon: <Icons.Home />,
    title: "Dashboard",
    routes: [
      {
        title: "Home",
        path: "/",
        exact: true,
        scopes: [],
      },
    ],
  },
  // 2. Discovery & Inventory
  {
    title: "Discovery & Inventory",
    icon: <Icons.DataAnalytics />,
    routes: [
      {
        title: "Dashboard",
        path: routes.DISCOVERY_INVENTORY_DASHBOARD_ROUTE,
        scopes: [],
        requiresPlus: true,
      },
      {
        title: "Activity Log",
        path: routes.ACTION_CENTER_ROUTE,
        scopes: [ScopeRegistryEnum.DISCOVERY_MONITOR_READ],
        requiresPlus: true,
        tabs: ACTION_CENTER_TAB_ITEMS,
      },
      {
        title: "Systems",
        path: routes.SYSTEM_ROUTE,
        scopes: [ScopeRegistryEnum.SYSTEM_READ],
      },
      {
        title: "Add Systems",
        path: routes.ADD_SYSTEMS_ROUTE,
        scopes: [ScopeRegistryEnum.SYSTEM_CREATE],
      },
      {
        title: "Datasets",
        path: routes.DATASET_ROUTE,
        scopes: [
          ScopeRegistryEnum.CTL_DATASET_CREATE,
          ScopeRegistryEnum.CTL_DATASET_UPDATE,
        ],
      },
      {
        title: "Data Catalog",
        path: routes.DATA_CATALOG_ROUTE,
        scopes: [ScopeRegistryEnum.DISCOVERY_MONITOR_READ],
        requiresFlag: "dataCatalog",
        requiresPlus: true,
      },
      {
        title: "Data Lineage",
        path: routes.DATAMAP_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.DATAMAP_READ],
      },
      {
        title: "Reports",
        path: routes.REPORTS_HUB_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.DATAMAP_READ],
      },
    ],
  },
  // 3. Consent
  {
    title: "Consent",
    icon: <Icons.SettingsAdjust />,
    routes: [
      {
        title: "Dashboard",
        path: routes.CONSENT_DASHBOARD_ROUTE,
        scopes: [],
        requiresPlus: true,
      },
      {
        title: "Consent Report",
        path: routes.CONSENT_REPORTING_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PRIVACY_NOTICE_READ],
      },
      {
        title: "Vendors",
        path: routes.CONFIGURE_CONSENT_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PRIVACY_NOTICE_READ],
      },
      {
        title: "Privacy Notices",
        path: routes.PRIVACY_NOTICES_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PRIVACY_NOTICE_READ],
      },
      {
        title: "Privacy Experiences",
        path: routes.PRIVACY_EXPERIENCE_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PRIVACY_EXPERIENCE_READ],
      },
      {
        title: "Consent Settings",
        path: routes.CONSENT_SETTINGS_HUB_ROUTE,
        requiresPlus: true,
        scopes: [ScopeRegistryEnum.PROPERTY_READ],
      },
    ],
  },
  // 4. Privacy Requests
  {
    title: "Privacy Requests",
    icon: <Icons.MessageQueue />,
    routes: [
      {
        title: "Dashboard",
        path: routes.PRIVACY_REQUESTS_DASHBOARD_ROUTE,
        scopes: [],
      },
      {
        title: "Request Manager",
        path: routes.PRIVACY_REQUESTS_ROUTE,
        scopes: [
          ScopeRegistryEnum.PRIVACY_REQUEST_READ,
          ScopeRegistryEnum.PRIVACY_REQUEST_CREATE,
          ScopeRegistryEnum.MANUAL_FIELD_READ_OWN,
          ScopeRegistryEnum.MANUAL_FIELD_READ_ALL,
        ],
        tabs: PRIVACY_REQUEST_TAB_ITEMS,
      },
      {
        title: "DSR Policies",
        path: routes.POLICIES_ROUTE,
        requiresFlag: "policies",
        scopes: [ScopeRegistryEnum.POLICY_READ],
      },
      {
        title: "Pre-approval Webhooks",
        path: routes.PRE_APPROVAL_WEBHOOKS_ROUTE,
        scopes: [
          ScopeRegistryEnum.WEBHOOK_READ,
          ScopeRegistryEnum.WEBHOOK_CREATE_OR_UPDATE,
        ],
      },
      {
        title: "Configuration",
        path: routes.PRIVACY_REQUESTS_CONFIGURATION_ROUTE,
        scopes: [ScopeRegistryEnum.PRIVACY_REQUEST_REDACTION_PATTERNS_UPDATE],
      },
    ],
  },
  // 5. AI Governance
  {
    title: "AI Governance",
    icon: <Icons.Document />,
    routes: [
      {
        title: "Dashboard",
        path: routes.AI_GOVERNANCE_DASHBOARD_ROUTE,
        scopes: [],
        requiresPlus: true,
        requiresFlag: "alphaPurposeBasedAccessControl",
      },
      {
        title: "Violation Log",
        path: routes.ACCESS_CONTROL_ROUTE,
        scopes: [ScopeRegistryEnum.DISCOVERY_MONITOR_READ],
        requiresFlag: "alphaPurposeBasedAccessControl",
        requiresPlus: true,
      },
      {
        title: "Access Policies",
        path: routes.ACCESS_POLICIES_ROUTE,
        requiresPlus: true,
        requiresFlag: "alphaPurposeBasedAccessControl",
        scopes: [],
      },
      {
        title: "Data Purposes",
        path: routes.DATA_PURPOSES_ROUTE,
        requiresPlus: true,
        requiresFlag: "alphaPurposeBasedAccessControl",
        scopes: [ScopeRegistryEnum.DATA_PURPOSE_READ],
      },
      {
        title: "Data Consumers",
        path: routes.DATA_CONSUMERS_ROUTE,
        requiresPlus: true,
        requiresFlag: "alphaPurposeBasedAccessControl",
        scopes: [ScopeRegistryEnum.DATA_CONSUMER_READ],
      },
      {
        title: "Privacy Assessments",
        path: routes.PRIVACY_ASSESSMENTS_ROUTE,
        scopes: [],
        requiresFlag: "privacyAssessments",
      },
    ],
  },
  // 6. Integrations
  {
    title: "Integrations",
    icon: <Icons.WorkflowAutomation />,
    routes: [
      {
        title: "Integration List",
        path: routes.INTEGRATION_MANAGEMENT_ROUTE,
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
        title: "Email Providers",
        path: routes.MESSAGING_PROVIDERS_ROUTE,
        scopes: [ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE],
      },
      {
        title: "Chat Providers",
        path: routes.CHAT_PROVIDERS_ROUTE,
        scopes: [ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE],
      },
    ],
  },
  // 7. Settings
  {
    title: "Settings",
    icon: <Icons.Settings />,
    routes: [
      {
        title: "Organization",
        path: routes.ORGANIZATION_MANAGEMENT_ROUTE,
        scopes: [
          ScopeRegistryEnum.ORGANIZATION_READ,
          ScopeRegistryEnum.ORGANIZATION_UPDATE,
        ],
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
        title: "User detail",
        path: routes.USER_DETAIL_ROUTE,
        hidden: true, // Don't show in nav but allow access
        scopes: [], // Any authenticated user can access their own profile
      },
      {
        title: "Role Management",
        path: routes.RBAC_ROUTE,
        requiresPlus: true,
        requiresFlag: "alphaRbac",
        scopes: [
          // Only Owners can access Role Management - they have assign_owners scope
          ScopeRegistryEnum.USER_PERMISSION_ASSIGN_OWNERS,
        ],
      },
      {
        title: "Notifications",
        path: routes.NOTIFICATIONS_ROUTE,
        scopes: [
          ScopeRegistryEnum.MESSAGING_TEMPLATE_UPDATE,
          ScopeRegistryEnum.DIGEST_CONFIG_READ,
          ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE,
        ],
        tabs: NOTIFICATION_TAB_ITEMS,
      },
      {
        title: "Custom fields",
        path: routes.CUSTOM_FIELDS_ROUTE,
        scopes: [ScopeRegistryEnum.CUSTOM_FIELD_READ],
        requiresPlus: true,
      },
      {
        title: "Taxonomy",
        path: routes.TAXONOMY_ROUTE,
        scopes: [
          ScopeRegistryEnum.DATA_USE_READ,
          ScopeRegistryEnum.DATA_CATEGORY_READ,
          ScopeRegistryEnum.DATA_SUBJECT_READ,
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
        title: "About Fides",
        path: routes.ABOUT_ROUTE,
        scopes: [ScopeRegistryEnum.USER_READ], // temporary scope while we don't have a scope for beta features
      },
    ],
  },
  // This section is meant to be hidden but accessible outside of dev builds
  // Any routes added in this section need to have hidden: true
  // to prevent them from being shown in the navigation
  {
    title: "Sandbox",
    icon: <Icons.Chemistry />,
    routes: [
      {
        title: "Privacy Notices Sandbox",
        path: routes.SANDBOX_PRIVACY_NOTICES_ROUTE,
        requiresFlag: "alphaPrivacyNoticesSandbox",
        scopes: [],
        hidden: true,
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
        title: "Prompt explorer",
        path: routes.PROMPT_EXPLORER_ROUTE,
        scopes: [ScopeRegistryEnum.DEVELOPER_READ],
        requiresPlus: true,
      },
      {
        title: "Seed data",
        path: routes.SEED_DATA_ROUTE,
        scopes: [ScopeRegistryEnum.DEVELOPER_READ],
        requiresPlus: true,
      },
      {
        title: "Test monitors",
        path: routes.TEST_MONITORS_ROUTE,
        scopes: [ScopeRegistryEnum.DEVELOPER_READ],
      },
      {
        title: "Ant design POC",
        path: routes.ANT_POC_ROUTE,
        scopes: [],
      },
      {
        title: "Fides JS docs",
        path: routes.FIDES_JS_DOCS,
        scopes: [],
      },
      {
        title: "Forms POC",
        path: routes.FORMS_POC_ROUTE,
        scopes: [],
      },
      {
        title: "Error test",
        path: routes.ERRORS_POC_ROUTE,
        scopes: [],
      },
    ],
  });
}

export interface NavGroupChild {
  title: string;
  path: string;
  exact?: boolean;
  hidden?: boolean;
  children: Array<NavGroupChild>;
  tabs?: NavConfigTab[];
}

export interface NavGroup {
  /**
   * Title of the group. Displayed in the IconRail navigation.
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
}

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

  // If the target route requires ANY of these flags (OR logic), check if at least one is enabled
  if (
    route.requiresAnyFlag &&
    (!flags || !route.requiresAnyFlag.some((flag) => flags[flag]))
  ) {
    return undefined;
  }

  // If the target route should be hidden when a specific flag is enabled, exclude it
  if (
    route.hidesIfFlag &&
    flags &&
    flags[route.hidesIfFlag] &&
    !window?.Cypress
  ) {
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
    hidden: route.hidden,
    children,
    tabs: route.tabs,
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

export interface ActiveNav extends NavGroup {
  path?: string;
}

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
