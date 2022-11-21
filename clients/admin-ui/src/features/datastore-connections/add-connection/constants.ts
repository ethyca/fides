import { ItemOption } from "common/dropdown/types";

import { SystemType } from "~/types/api";

import { DATASTORE_CONNECTION_ROUTE } from "../../../constants";
import { AddConnectionStep, ConnectorParameterOption } from "./types";

export enum ConfigurationSettings {
  CONNECTOR_PARAMETERS = "Connector parameters",
  DATASET_CONFIGURATION = "Dataset configuration",
  DSR_CUSTOMIZATION = "DSR customization",
}

export const CONNECTION_TYPE_FILTER_MAP = new Map<string, ItemOption>([
  ["Manual connectors", { value: SystemType.MANUAL }],
  [
    "Database",
    {
      value: SystemType.DATABASE.toString(),
    },
  ],
  ["3rd party integrations", { value: SystemType.SAAS.toString() }],
  ["Show all", { value: "" }],
]);

export const CONNECTOR_PARAMETERS_OPTIONS: ConnectorParameterOption[] = [
  {
    type: SystemType.DATABASE,
    options: [
      ConfigurationSettings.CONNECTOR_PARAMETERS,
      ConfigurationSettings.DATASET_CONFIGURATION,
    ],
  },
  {
    type: SystemType.MANUAL,
    options: [
      ConfigurationSettings.CONNECTOR_PARAMETERS,
      ConfigurationSettings.DSR_CUSTOMIZATION,
    ],
  },
  {
    type: SystemType.SAAS,
    options: [
      ConfigurationSettings.CONNECTOR_PARAMETERS,
      ConfigurationSettings.DATASET_CONFIGURATION,
    ],
  },
];

export const DEFAULT_CONNECTION_TYPE_FILTER = CONNECTION_TYPE_FILTER_MAP.get(
  "Show all"
)?.value as string;

export const STEPS: AddConnectionStep[] = [
  {
    stepId: 0,
    label: "Connections",
    href: DATASTORE_CONNECTION_ROUTE,
  },
  {
    stepId: 1,
    label: "Choose your connection",
    href: `${DATASTORE_CONNECTION_ROUTE}/new?step=1`,
    description:
      "Systems describe any services that store or process data for your organization, including third-party APIs, web applications, databases, and data warehouses. System discovery allows Fides to identify and build a data map from the list of systems that exist within your organization.",
    parentStepId: 0,
  },
  {
    stepId: 2,
    label: "Configure your {identifier} connection",
    href: `${DATASTORE_CONNECTION_ROUTE}/new?step=2`,
    parentStepId: 1,
  },
  {
    stepId: 3,
    label: "Configure your {identifier} connection",
    href: `${DATASTORE_CONNECTION_ROUTE}/new?step=3`,
    parentStepId: 1,
  },
];
