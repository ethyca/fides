import { NextApiRequest } from "next";

export const createLoggingContext = (request: NextApiRequest) => {
  const id = request.headers["x-request-id"] ?? "null";
  const logSuffix = `| { "Request-Id": ${id} }`;
  const debug = (...args: Parameters<typeof console.debug>) =>
    // eslint-disable-next-line no-console
    console.debug(...args, logSuffix);
  const log = (...args: Parameters<typeof console.log>) =>
    // eslint-disable-next-line no-console
    console.log(...args, logSuffix);

  return {
    debug,
    log,
  };
};

export type LoggerContext = ReturnType<typeof createLoggingContext>;
