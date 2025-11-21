import { taxonomyHandlers } from "~/features/taxonomy/taxonomy.mocks";

import { discoveryMonitorHandlers } from "./action-center/handlers";

// eslint-disable-next-line import/prefer-default-export
export const handlers = [...taxonomyHandlers(), ...discoveryMonitorHandlers()];
