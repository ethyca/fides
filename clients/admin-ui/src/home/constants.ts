import {
  CONFIG_WIZARD_ROUTE,
  DATAMAP_ROUTE,
  DATASTORE_CONNECTION_ROUTE,
  PRIVACY_REQUESTS_ROUTE,
  SYSTEM_ROUTE,
} from "~/constants";
import { ScopeRegistryEnum } from "~/types/api";

import { ModuleCardConfig } from "./types";

/**
 * Enums
 */
export enum ModuleCardKeys {
  ADD_SYSTEMS = 1,
  VIEW_SYSTEMS = 2,
  CONFIGURE_PRIVACY_REQUESTS = 3,
  REVIEW_PRIVACY_REQUESTS = 4,
  VIEW_MAP = 5,
}

export const MODULE_CARD_ITEMS: ModuleCardConfig[] = [
  {
    color: "blue",
    description:
      "Explore the systems and data flow across your organization and create custom reports.",
    href: `${DATAMAP_ROUTE}`,
    key: ModuleCardKeys.VIEW_MAP,
    name: "View data map",
    sortOrder: 0,
    title: "VM",
    requiresPlus: true,
    requiresSystems: true,
    scopes: [ScopeRegistryEnum.DATAMAP_READ],
  },
  {
    color: "orange",
    description:
      "As your organization grows you can continue adding systems to your Fides data map.",
    href: `${CONFIG_WIZARD_ROUTE}`,
    key: ModuleCardKeys.ADD_SYSTEMS,
    name: "Add systems",
    sortOrder: 1,
    title: "AS",
    scopes: [ScopeRegistryEnum.CLI_OBJECTS_CREATE],
  },
  {
    color: "purple",
    description:
      "Review system information for all systems in your organization",
    href: `${SYSTEM_ROUTE}`,
    key: ModuleCardKeys.VIEW_SYSTEMS,
    name: "View systems",
    sortOrder: 2,
    title: "VS",
    scopes: [ScopeRegistryEnum.CLI_OBJECTS_READ],
    requiresSystems: true,
  },
  {
    color: "teal",
    description:
      "Connect your systems and configure privacy request processing for DSRs (access and erasure).",
    href: `${DATASTORE_CONNECTION_ROUTE}/new?step=1`,
    key: ModuleCardKeys.CONFIGURE_PRIVACY_REQUESTS,
    name: "Configure privacy requests",
    sortOrder: 3,
    title: "PR",
    scopes: [ScopeRegistryEnum.CONNECTION_CREATE_OR_UPDATE],
  },

  {
    color: "pink",
    description:
      "Review, approve and process privacy requests across your systems on behalf of your users.",
    href: `${PRIVACY_REQUESTS_ROUTE}`,
    key: ModuleCardKeys.REVIEW_PRIVACY_REQUESTS,
    name: "Review privacy requests",
    sortOrder: 4,
    title: "RP",
    scopes: [ScopeRegistryEnum.PRIVACY_REQUEST_REVIEW],
    requiresConnections: true,
  },
];
