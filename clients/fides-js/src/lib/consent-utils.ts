import {
  FidesOptions,
  UserGeolocation,
  VALID_ISO_3166_LOCATION_REGEX,
} from "./consent-types";

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
 * Construct user location str to be ingested by Fides API
 * Returns null if geolocation cannot be constructed by provided params, e.g. us_ca
 */
export const constructFidesRegionString = (
  geoLocation?: UserGeolocation | null,
  debug: boolean = false
): string | null => {
  debugLog(debug, "constructing geolocation...");
  if (!geoLocation) {
    debugLog(
      debug,
      "cannot construct user location since geoLocation is undefined or null"
    );
    return null;
  }
  if (
    geoLocation.location &&
    VALID_ISO_3166_LOCATION_REGEX.test(geoLocation.location)
  ) {
    // Fides backend requires underscore deliminator
    return geoLocation.location.replace("-", "_").toLowerCase();
  }
  if (geoLocation.country && geoLocation.region) {
    return `${geoLocation.country.toLowerCase()}_${geoLocation.region.toLowerCase()}`;
  }
  // todo: return geoLocation.country when BE supports filtering by just country
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

  if (!options.fidesApiUrl) {
    debugLog(options.debug, "Invalid options: fidesApiUrl is required!");
    return false;
  }

  if (!options.privacyCenterUrl) {
    debugLog(options.debug, "Invalid options: privacyCenterUrl is required!");
    return false;
  }

  try {
    // eslint-disable-next-line no-new
    new URL(options.privacyCenterUrl);
    // eslint-disable-next-line no-new
    new URL(options.fidesApiUrl);
  } catch (e) {
    debugLog(
      options.debug,
      "Invalid options: privacyCenterUrl or fidesApiUrl is an invalid URL!",
      options.privacyCenterUrl
    );
    return false;
  }

  return true;
};
