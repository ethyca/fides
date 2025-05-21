import pino from "pino";

import { LogLevels } from "./PrivacyCenterSettings";

export const createLogger = ({ logLevel }: { logLevel: LogLevels }) => {
  const logger = pino({
    level: logLevel,
  });

  return logger;
};
