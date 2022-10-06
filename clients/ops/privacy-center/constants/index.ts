/* eslint-disable import/prefer-default-export */


import config from "../config/config.json";

// Compute the host URL for the server, while being backwards compatible with
// the previous "fidesops_host_***" configuration
export const hostUrl =
  process.env.NODE_ENV === "development"
    ? (config.server_url_development || (config as any).fidesops_host_development)
    : (config.server_url_production || (config as any).fidesops_host_production);