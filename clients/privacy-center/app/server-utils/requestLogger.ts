import { NextApiRequest } from "next";

import { createLogger } from "./logger";

export const createRequestLogger = (request: NextApiRequest) => {
  const id = request.headers["x-request-id"] ?? "null";
  const child = createLogger().child({
    requestId: id,
  });
  return child;
};

export type LoggerContext = ReturnType<typeof createRequestLogger>;
