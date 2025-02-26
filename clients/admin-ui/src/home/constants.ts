import palette from "fidesui/src/palette/palette.module.scss";

import {
  ADD_SYSTEMS_ROUTE,
  CONFIGURE_CONSENT_ROUTE,
  DATAMAP_ROUTE,
  PRIVACY_REQUESTS_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";
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
    color: palette.FIDESUI_SANDSTONE,
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
    color: palette.FIDESUI_OLIVE,
    description: "Add third party applications and databases to your data map",
    href: `${ADD_SYSTEMS_ROUTE}`,
    key: ModuleCardKeys.ADD_SYSTEMS,
    name: "Add systems",
    sortOrder: 1,
    title: "AS",
    scopes: [ScopeRegistryEnum.SYSTEM_CREATE],
  },
  {
    color: palette.FIDESUI_TERRACOTTA,
    description:
      "Review system information for all systems in your organization",
    href: `${SYSTEM_ROUTE}`,
    key: ModuleCardKeys.VIEW_SYSTEMS,
    name: "View systems",
    sortOrder: 2,
    title: "VS",
    scopes: [ScopeRegistryEnum.SYSTEM_READ],
    requiresSystems: true,
  },
  {
    color: palette.FIDESUI_MINOS,
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
  {
    color: palette.FIDESUI_NECTAR,
    description:
      "Manage privacy notices and experiences for all domains in your organization",
    href: `${CONFIGURE_CONSENT_ROUTE}`,
    key: ModuleCardKeys.CONFIGURE_CONSENT,
    name: "Manage consent",
    sortOrder: 5,
    title: "MC",
    scopes: [ScopeRegistryEnum.PRIVACY_NOTICE_READ],
    requiresPlus: true,
  },
];
