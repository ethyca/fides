import { ItemOption } from "common/dropdown/types";
import { SystemType } from "datastore-connections/constants";

import { DATASTORE_CONNECTION_ROUTE } from "../../../constants";
import { AddConnectionStep } from "./types";

export const CONNECTION_TYPE_FILTER_MAP = new Map<string, ItemOption>([
  [
    "Database connectors",
    {
      isDisabled: true,
      toolTip: `You cannot add database connections from here at this time. Please refer to our documentation on how you can do so from our API.`,
      value: SystemType.DATABASE.toString(),
    },
  ],
  ["Third party connectors", { value: SystemType.SAAS.toString() }],
  // TODO: Uncomment the following when Database connectors are supported
  // ["Show all", { value: "" }],
]);

// TODO: Update this to Show all when Database connectors are supported
export const DEFAULT_CONNECTION_TYPE_FILTER = CONNECTION_TYPE_FILTER_MAP.get(
  "Third party connectors"
)?.value;

export const STEPS: AddConnectionStep[] = [
  {
    stepId: 0,
    label: "Datastore Connections",
    href: DATASTORE_CONNECTION_ROUTE,
  },
  {
    stepId: 1,
    label: "Choose your connection",
    href: `${DATASTORE_CONNECTION_ROUTE}/new`,
    description:
      "The building blocks of your data map are the list of systems that exist in your organization. Think of systems as as anything that might store or process data in your organization, from a web application, to a database, or data warehouse.",
    parentStepId: 1,
  },
];
