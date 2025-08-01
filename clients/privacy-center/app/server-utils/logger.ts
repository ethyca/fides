import type { LoggerOptions } from "pino";
import pino from "pino";

import loadEnvironmentVariables from "./loadEnvironmentVariables";

export const createLogger = (options?: LoggerOptions) => {
  const settings = loadEnvironmentVariables();
  const isServer = typeof window === "undefined";
  const isNextEdgeRuntime = process.env.NEXT_RUNTIME === "edge";
  const logLevel =
    process.env.NODE_ENV === "development" ? "debug" : settings.LOG_LEVEL;

  const logger = pino({
    // Standard pino config
    ...{ level: logLevel },
    // Detect Next "edge" runtime environment and force consistent JSON format despite using a "console" logger
    // See https://github.com/vercel/next.js/discussions/33898 for issue details
    // See https://www.trysmudford.com/blog/nextjs-edge-logging/ for solution below
    ...(isServer &&
      isNextEdgeRuntime && {
        browser: {
          write: {
            /* eslint-disable no-console */
            critical: (o: unknown) => console.error(JSON.stringify(o)),
            debug: (o: unknown) => console.log(JSON.stringify(o)),
            error: (o: unknown) => console.error(JSON.stringify(o)),
            fatal: (o: unknown) => console.error(JSON.stringify(o)),
            info: (o: unknown) => console.log(JSON.stringify(o)),
            trace: (o: unknown) => console.log(JSON.stringify(o)),
            warn: (o: unknown) => console.warn(JSON.stringify(o)),
            /* eslint-enable no-console */
          },
        },
      }),
    ...options,
  });

  return logger;
};
