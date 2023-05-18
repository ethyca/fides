import { FidesOptions, UserGeolocation } from "./consent-types";

/**
 * Wrapper around 'console.log' that only logs output when the 'debug' banner
 * option is truthy
 */
type ConsoleLogParameters = Parameters<typeof console.log>;
export const debugLog = (
  enabled: boolean,
  ...args: ConsoleLogParameters
): void => {
  if (enabled) {
    // eslint-disable-next-line no-console
    console.log(...args);
  }
};

/**
 * Construct user geolocation str to be ingested by Fides API
 * Returns null if geolocation cannot be constructed by provided params
 */
export const constructLocation = (
  geoLocation?: UserGeolocation,
  debug: boolean = false
): string | null => {
  debugLog(debug, "constructing geolocation...");
  if (!geoLocation) {
    debugLog(
      debug,
      "cannot construct user location since geoLocation is undefined"
    );
    return null;
  }
  if (geoLocation.location) {
    return geoLocation.location;
  }
  if (geoLocation.country && geoLocation.region) {
    return `${geoLocation.country}-${geoLocation.region}`;
  }
  if (geoLocation.country) {
    return geoLocation.country;
  }
  debugLog(
    debug,
    "cannot construct user location from provided geoLocation params..."
  );
  return null;
};

/**
 * Validate the fides global config options
 */
export const validateOptions = (options: FidesOptions): boolean => {
  // Check if options is an invalid type
  if (options === undefined || typeof options !== "object") {
    return false;
  }
  // todo- more validation here?

  if (!options.privacyCenterUrl) {
    debugLog(options.debug, "Invalid options: privacyCenterUrl is required!");
    return false;
  }

  if (options.privacyCenterUrl) {
    try {
      // eslint-disable-next-line no-new
      new URL(options.privacyCenterUrl);
    } catch (e) {
      debugLog(
        options.debug,
        "Invalid options: privacyCenterUrl is an invalid URL!",
        options.privacyCenterUrl
      );
      return false;
    }
  }

  return true;
};
