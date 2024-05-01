import type { NextApiRequest, NextApiResponse } from "next";

import type { PrivacyCenterEnvironment } from "~/app/server-environment";
import {
  CLOUDFRONT_HEADER_COUNTRY,
  CLOUDFRONT_HEADER_REGION,
} from "~/common/geolocation";

/**
 * Implements a basic wrapper around the Console module for *semi*-structured
 * logging from Privacy Center. This is designed to be easily replaced by a real
 * logger like `pino`.
 */
export function debugLog(
  message: string,
  context: { req?: NextApiRequest; res?: NextApiResponse; [key: string]: any }
) {
  // TODO: ensure this LOG_LEVEL env var is forwards-compatible with a real logger
  // TODO: load this LOG_LEVEL env var through a server-environment helper
  if (process.env.FIDES_PRIVACY_CENTER__LOG_LEVEL === "DEBUG") {
    // NOTE: in a real JSON logger, we wouldn't stringify this ourselves ;)
    const { req, res, ...other } = context;
    let log: any = {
      level: 10, // 10 === DEBUG-level log in most frameworks (Pino, Python, etc.)
      msg: message,
    };
    // Add Request context
    if (req) {
      log = {
        ...log,
        method: req.method,
        query: req.query,
        [`headers[${CLOUDFRONT_HEADER_COUNTRY}]`]:
          req.headers[CLOUDFRONT_HEADER_COUNTRY] || "",
        [`headers[${CLOUDFRONT_HEADER_REGION}]`]:
          req.headers[CLOUDFRONT_HEADER_REGION] || "",
      };
    }
    // Add Response context
    if (res) {
      log = {
        ...log,
        statusCode: res.statusCode,
      };
    }
    // Add custom context
    if (other) {
      log = {
        ...log,
        ...other,
      };
    }
    // Write the log as a JSON string
    // eslint-disable-next-line no-console
    console.log(JSON.stringify(log));
  }
}
