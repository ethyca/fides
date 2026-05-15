import { taxonomyHandlers } from "~/features/taxonomy/taxonomy.mocks";

import { agentChatHandlers } from "./access-policies/agent-chat-handlers";
import { accessPoliciesHandlers } from "./access-policies/handlers";
import { discoveryMonitorHandlers } from "./action-center/handlers";
import { dashboardHandlers } from "./dashboard/handlers";
import { dashboardGraphqlHandlers } from "./dashboard-graphql/handlers";
import { dataPurposesHandlers } from "./data-purposes/handlers";
import { manualTasksHandlers } from "./manual-tasks/handlers";
import { policyHandlers } from "./policy/handlers";

const restMocksEnabled = process.env.NEXT_PUBLIC_MOCK_API === "true";
const graphqlMocksEnabled = process.env.NEXT_PUBLIC_MOCK_GRAPHQL === "true";

// eslint-disable-next-line import/prefer-default-export
export const handlers = [
  // GraphQL handler is independently toggled so the dashboard PoC can mock
  // the GraphQL endpoint while the rest of the app talks to the real BE.
  ...(graphqlMocksEnabled ? dashboardGraphqlHandlers() : []),
  ...(restMocksEnabled
    ? [
        ...taxonomyHandlers(),
        ...discoveryMonitorHandlers(),
        ...policyHandlers(),
        ...accessPoliciesHandlers(),
        ...agentChatHandlers(),
        ...dashboardHandlers(),
        ...manualTasksHandlers(),
        ...dataPurposesHandlers(),
      ]
    : []),
];
