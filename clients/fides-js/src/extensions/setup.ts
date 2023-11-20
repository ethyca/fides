import type { FidesOptions } from "../lib/consent-types";

/**
 * The path where the GPP extension bundle is located,
 * likely served by the privacy center
 */
const GPP_EXT_PATH = "/gpp-ext.js";

export const setupExtensions = (options: FidesOptions) => {
  if (options.gppEnabled) {
    import(GPP_EXT_PATH).catch((e) => {
      // eslint-disable-next-line no-console
      console.error("Unable to import GPP extension", e);
    });
  }
};
