import { NextApiRequest } from "next";
import pino from "pino";

import { loadServerSettings } from "../server-environment";

export const createLogger = () => {
  const settings = loadServerSettings();
  const logger = pino({
    level: settings.LOG_LEVEL,
    transport: { target: "pino-pretty" },
  });

  return logger;
};

export const createRequestLogger = (request: NextApiRequest) => {
  const id = request.headers["x-request-id"] ?? "null";
  const child = createLogger().child({ "Request-Id": id });
  return child;
};

export type LoggerContext = ReturnType<typeof createRequestLogger>;
