import { NextApiRequest } from "next";
import pino from "pino";

export const createLoggingContext = (request: NextApiRequest) => {
  const id = request.headers["x-request-id"] ?? "null";
  const logSuffix = `| { "Request-Id": ${id} }`;
  const logger = pino({ level: "info" });
  const child = logger.child({ "Request-Id": id });

  return child;
};

export type LoggerContext = ReturnType<typeof createLoggingContext>;
