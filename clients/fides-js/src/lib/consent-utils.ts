import {
  ComponentType,
  ConsentMechanism,
  FidesOptions,
  PrivacyExperience,
  UserConsentPreference,
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
 * Convert a user consent preference into true/false
 */
export const transformUserPreferenceToBoolean = (
  preference: UserConsentPreference | undefined
) => {
  if (!preference) {
    return false;
  }
  if (preference === UserConsentPreference.OPT_OUT) {
    return false;
  }
  if (preference === UserConsentPreference.OPT_IN) {
    return true;
  }
  return preference === UserConsentPreference.ACKNOWLEDGE;
};

/**
 * Convert a true/false consent to Fides user consent preference
 */
export const transformConsentToFidesUserPreference = (
  consented: boolean,
  consentMechanism?: ConsentMechanism
): UserConsentPreference => {
  if (consented) {
    if (consentMechanism === ConsentMechanism.NOTICE_ONLY) {
      return UserConsentPreference.ACKNOWLEDGE;
    }
    return UserConsentPreference.OPT_IN;
  }
  return UserConsentPreference.OPT_OUT;
};

/**
 * Validate the fides global config options. If invalid, we cannot make API calls to Fides or link to the Privacy Center.
 */
export const validateOptions = (options: FidesOptions): boolean => {
  // Check if options is an invalid type
  debugLog(
    options.debug,
    "Validating Fides consent overlay options...",
    options
  );
  if (typeof options !== "object") {
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

/**
 * Determines whether experience is valid and relevant notices exist within the experience
 */
export const experienceIsValid = (
  effectiveExperience: PrivacyExperience | undefined | null,
  options: FidesOptions
): boolean => {
  if (!effectiveExperience) {
    debugLog(
      options.debug,
      `No relevant experience found. Skipping overlay initialization.`
    );
    return false;
  }
  if (
    !(
      effectiveExperience.privacy_notices &&
      effectiveExperience.privacy_notices.length >= 0
    )
  ) {
    debugLog(
      options.debug,
      `No relevant notices in the privacy experience. Skipping overlay initialization.`,
      effectiveExperience
    );
    return false;
  }
  if (effectiveExperience.component !== ComponentType.OVERLAY) {
    debugLog(
      options.debug,
      "No experience found with overlay component. Skipping overlay initialization."
    );
    return false;
  }
  if (!effectiveExperience.experience_config) {
    debugLog(
      options.debug,
      "No experience config found with for experience. Skipping overlay initialization."
    );
    return false;
  }

  return true;
};
