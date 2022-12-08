/* eslint-disable import/prefer-default-export */

import { Config } from "~/types/config";
import configJson from "~/config/config.json";

export const config: Config = configJson;

// Compute the host URL for the server, while being backwards compatible with
// the previous "fidesops_host_***" configuration
// DEFER: remove backwards compatibility (see https://github.com/ethyca/fides/issues/1264)
export const hostUrl =
  process.env.NODE_ENV === "development" || process.env.NODE_ENV === "test"
    ? config.server_url_development || (config as any).fidesops_host_development
    : config.server_url_production || (config as any).fidesops_host_production;
