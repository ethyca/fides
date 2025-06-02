import pino from "pino";

import loadEnvironmentVariables from "./loadEnvironmentVariables";

export const createLogger = () => {
  const settings = loadEnvironmentVariables();
  const logger = pino({
    level: settings.LOG_LEVEL,
  });

  return logger;
};
