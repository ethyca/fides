import { taxonomyHandlers } from "~/features/taxonomy/taxonomy.mocks";

import { discoveryMonitorHandlers } from "./action-center/handlers";
import { policyHandlers } from "./policy/handlers";
import { systemLinksHandlers } from "./system-links/handlers";

// eslint-disable-next-line import/prefer-default-export
export const handlers = [
  ...taxonomyHandlers(),
  ...discoveryMonitorHandlers(),
  ...policyHandlers(),
  ...systemLinksHandlers(),
];
