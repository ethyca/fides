import { NextApiRequest } from "next";

import { loadServerSettings } from "../server-environment";
import { createLogger } from "./logger";

export const createRequestLogger = (request: NextApiRequest) => {
  const serverSettings = loadServerSettings();
  const id = request.headers["x-request-id"] ?? "null";
  const child = createLogger({ logLevel: serverSettings.LOG_LEVEL }).child({
    requestId: id,
  });
  return child;
};

export type LoggerContext = ReturnType<typeof createRequestLogger>;
