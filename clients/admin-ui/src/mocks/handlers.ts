import { rest } from "msw";

import { taxonomyHandlers } from "~/features/taxonomy/taxonomy.mocks";

// eslint-disable-next-line import/prefer-default-export
export const handlers = [...taxonomyHandlers()];
