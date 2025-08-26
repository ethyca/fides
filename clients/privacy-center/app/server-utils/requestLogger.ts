import { NextApiRequest } from "next";

import { createLogger } from "./logger";

export const createRequestLogger = (request: NextApiRequest) => {
  const isDevelopment = process.env.NODE_ENV === "development";
  const id = request.headers?.["x-request-id"] ?? "null";
  const child = createLogger(
    isDevelopment
      ? {
          transport: {
            target: "pino-pretty",
            options: {
              ignore: "version,requestId",
              levelFirst: true,
            },
          },
        }
      : {},
  ).child({
    requestId: id,
    version: process.env.version,
  });
  return child;
};

export type LoggerContext = ReturnType<typeof createRequestLogger>;
