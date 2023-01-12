import {
  CONFIG_WIZARD_ROUTE,
  DATASTORE_CONNECTION_ROUTE,
  PRIVACY_REQUESTS_ROUTE,
  SYSTEM_ROUTE,
} from "~/constants";

import { ModuleCard } from "./types";

/**
 * Enums
 */
export enum ModuleCardKeys {
  ADD_SYSTEMS = 1,
  MANAGE_SYSTEMS = 2,
  CONFIGURE_PRIVACY_REQUESTS = 3,
  REVIEW_PRIVACY_REQUESTS = 4,
}

export const MODULE_CARD_ITEMS: ModuleCard[] = [
  {
    backgroundColor: "orange.50",
    description:
      "As your organization grows you can continue adding systems to your Fides data map.",
    descriptionColor: "gray.500",
    hoverBorderColor: "orange.500",
    href: `${CONFIG_WIZARD_ROUTE}`,
    key: ModuleCardKeys.ADD_SYSTEMS,
    name: "Add systems",
    nameColor: "orange.800",
    sortOrder: 1,
    title: "AS",
    titleColor: "orange.300",
  },
  {
    backgroundColor: "purple.50",
    description:
      "Review and update system information across your data map including data categories and purposes of processing.",
    descriptionColor: "gray.500",
    hoverBorderColor: "purple.500",
    href: `${SYSTEM_ROUTE}`,
    key: ModuleCardKeys.MANAGE_SYSTEMS,
    name: "Manage systems",
    nameColor: "purple.800",
    sortOrder: 2,
    title: "MS",
    titleColor: "purple.300",
  },
  {
    backgroundColor: "teal.50",
    description:
      "Connect your systems and configure privacy request processing for DSRs (access and erasure).",
    descriptionColor: "gray.500",
    hoverBorderColor: "teal.500",
    href: `${DATASTORE_CONNECTION_ROUTE}/new?step=1`,
    key: ModuleCardKeys.CONFIGURE_PRIVACY_REQUESTS,
    name: "Configure privacy requests",
    nameColor: "teal.800",
    sortOrder: 3,
    title: "PR",
    titleColor: "teal.300",
  },

  {
    backgroundColor: "pink.50",
    description:
      "Review, approve and process privacy requests across your systems on behalf of your users.",
    descriptionColor: "gray.500",
    hoverBorderColor: "pink.500",
    href: `${PRIVACY_REQUESTS_ROUTE}`,
    key: ModuleCardKeys.REVIEW_PRIVACY_REQUESTS,
    name: "Review privacy requests",
    nameColor: "pink.800",
    sortOrder: 4,
    title: "RP",
    titleColor: "pink.300",
  },
];
