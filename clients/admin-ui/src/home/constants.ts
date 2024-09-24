import {
  ADD_SYSTEMS_ROUTE,
  CONFIGURE_CONSENT_ROUTE,
  DATAMAP_ROUTE,
  PRIVACY_REQUESTS_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/v2/routes";
import { ScopeRegistryEnum } from "~/types/api";

import { ModuleCardConfig } from "./types";

/**
 * Enums
 */
export enum ModuleCardKeys {
  ADD_SYSTEMS = 1,
  VIEW_SYSTEMS = 2,
  REVIEW_PRIVACY_REQUESTS = 3,
  VIEW_MAP = 4,
  CONFIGURE_CONSENT = 5,
}

export const MODULE_CARD_ITEMS: ModuleCardConfig[] = [
  {
    color: "sandstone",
    description:
      "Explore the systems and data flow across your organization and create custom reports.",
    href: `${DATAMAP_ROUTE}`,
    key: ModuleCardKeys.VIEW_MAP,
    name: "View data map",
    sortOrder: 0,
    requiresPlus: true,
    requiresSystems: true,
    scopes: [ScopeRegistryEnum.DATAMAP_READ],
  },
  {
    color: "olive",
    description: "Add third party applications and databases to your data map",
    href: `${ADD_SYSTEMS_ROUTE}`,
    key: ModuleCardKeys.ADD_SYSTEMS,
    name: "Add systems",
    sortOrder: 1,
    scopes: [ScopeRegistryEnum.SYSTEM_CREATE],
  },
  {
    color: "terracotta",
    description:
      "Review system information for all systems in your organization",
    href: `${SYSTEM_ROUTE}`,
    key: ModuleCardKeys.VIEW_SYSTEMS,
    name: "View systems",
    sortOrder: 2,
    scopes: [ScopeRegistryEnum.SYSTEM_READ],
    requiresSystems: true,
  },
  {
    color: "minos",
    description:
      "Review, approve and process privacy requests across your systems on behalf of your users.",
    href: `${PRIVACY_REQUESTS_ROUTE}`,
    key: ModuleCardKeys.REVIEW_PRIVACY_REQUESTS,
    name: "Review privacy requests",
    sortOrder: 4,
    scopes: [ScopeRegistryEnum.PRIVACY_REQUEST_REVIEW],
    requiresConnections: true,
  },
  {
    color: "nectar",
    description:
      "Manage privacy notices and experiences for all domains in your organization",
    href: `${CONFIGURE_CONSENT_ROUTE}`,
    key: ModuleCardKeys.CONFIGURE_CONSENT,
    name: "Manage consent",
    sortOrder: 5,
    scopes: [ScopeRegistryEnum.PRIVACY_NOTICE_READ],
    requiresPlus: true,
  },
];
