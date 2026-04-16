import { taxonomyHandlers } from "~/features/taxonomy/taxonomy.mocks";

import { accessPoliciesHandlers } from "./access-policies/handlers";
import { discoveryMonitorHandlers } from "./action-center/handlers";
import { dashboardHandlers } from "./dashboard/handlers";
import { manualTasksHandlers } from "./manual-tasks/handlers";
import { policyHandlers } from "./policy/handlers";

// eslint-disable-next-line import/prefer-default-export
export const handlers = [
  ...taxonomyHandlers(),
  ...discoveryMonitorHandlers(),
  ...policyHandlers(),
  ...accessPoliciesHandlers(),
  ...dashboardHandlers(),
  ...manualTasksHandlers(),
];
