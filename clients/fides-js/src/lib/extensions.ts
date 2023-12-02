import type { FidesOptions } from "./consent-types";

export const setupExtensions = async (options: FidesOptions) => {
  if (options.gppEnabled) {
    try {
      await import(options.gppExtensionPath);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error("Unable to import GPP extension", e);
    }
  }
};
