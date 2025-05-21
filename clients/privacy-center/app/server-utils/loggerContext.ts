import { NextApiRequest } from "next";
import pino from "pino";
import { loadServerSettings } from "../server-environment";

export const createLoggingContext = (request: NextApiRequest) => {
  const settings = loadServerSettings();
  const id = request.headers["x-request-id"] ?? "null";
  const logger = pino({
    level: settings.LOG_LEVEL,
    transport: { target: "pino-pretty" },
  });
  const child = logger.child({ "Request-Id": id });

  return child;
};

export type LoggerContext = ReturnType<typeof createLoggingContext>;
