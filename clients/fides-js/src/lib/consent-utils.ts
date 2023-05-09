import { ConsentBannerOptions } from "./consent-types";

/**
 * Configuration options used for the consent banner. The default values (below)
 * will be mutated by the banner() function to override with any user-provided
 * options at runtime.
 *
 * This is effectively a global variable, but we provide getter/setter functions
 * to make it seem safer and only export the getBannerOptions() one outside this
 * module.
 */
// todo- refactor to consent experience options
let globalBannerOptions: ConsentBannerOptions = {
  debug: true,
  isDisabled: false,
  isGeolocationEnabled: false,
  geolocationApiUrl: "http://dev-cdn-api.ethyca.com/location",
  labels: {
    bannerDescription:
      "This website processes your data respectfully, so we require your consent to use cookies.",
    primaryButton: "Accept All",
    secondaryButton: "Reject All",
    tertiaryButton: "Manage Preferences",
  },
  privacyCenterUrl: "http://localhost:3000", // TODO: default?
};

/**
 * Change the consent banner options.
 *
 * WARNING: If called after `banner()` has already ran, many of these options
 * will no longer take effect!
 */
export const setBannerOptions = (options: ConsentBannerOptions): void => {
  globalBannerOptions = options;
};

/**
 * Get the configured options for the consent banner
 */
export const getBannerOptions = (): ConsentBannerOptions => globalBannerOptions;

/**
 * Wrapper around 'console.log' that only logs output when the 'debug' banner
 * option is truthy
 */
type ConsoleLogParameters = Parameters<typeof console.log>;
export const debugLog = (...args: ConsoleLogParameters): void => {
  if (getBannerOptions().debug) {
    // eslint-disable-next-line no-console
    console.log(...args); // TODO: use console.debug instead?
  }
};
