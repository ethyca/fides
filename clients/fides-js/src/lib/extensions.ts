import type { FidesOptions } from "./consent-types";

/**
 * The path where the GPP extension bundle is located,
 * likely served by the privacy center
 */
const GPP_EXT_PATH = "/fides-ext-gpp.js";

export const setupExtensions = async (options: FidesOptions) => {
  if (options.gppEnabled) {
    try {
      await import(GPP_EXT_PATH);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error("Unable to import GPP extension", e);
    }
  }
};
