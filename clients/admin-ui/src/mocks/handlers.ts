import { taxonomyHandlers } from "~/features/taxonomy/taxonomy.mocks";

import { agentChatHandlers } from "./access-policies/agent-chat-handlers";
import { accessPoliciesHandlers } from "./access-policies/handlers";
import { discoveryMonitorHandlers } from "./action-center/handlers";
import { dashboardHandlers } from "./dashboard/handlers";
import { dataPurposesHandlers } from "./data-purposes/handlers";
import { manualTasksHandlers } from "./manual-tasks/handlers";
import { policyHandlers } from "./policy/handlers";

export const handlers = [
  ...taxonomyHandlers(),
  ...discoveryMonitorHandlers(),
  ...policyHandlers(),
  ...accessPoliciesHandlers(),
  ...agentChatHandlers(),
  ...dashboardHandlers(),
  ...manualTasksHandlers(),
  ...dataPurposesHandlers(),
];
