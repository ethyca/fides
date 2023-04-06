/* eslint-disable import/prefer-default-export */

import { Config, IdentityInputs } from "~/types/config";
import configJson from "~/config/config.json";
import testConfigJson from "~/config/test-config.json";

export const config: Config = process.env.NEXT_PUBLIC_APP_ENV === "test" ? testConfigJson : configJson;

// Compute the host URL for the server, while being backwards compatible with
// the previous "fidesops_host_***" configuration
// DEFER: remove backwards compatibility (see https://github.com/ethyca/fides/issues/1264)
export const hostUrl =
  process.env.NODE_ENV === "development" || process.env.NODE_ENV === "test"
    ? config.server_url_development || (config as any).fidesops_host_development
    : config.server_url_production || (config as any).fidesops_host_production;

export const defaultIdentityInput: IdentityInputs = { email: "optional" };
