import {
  FidesConfig,
  FidesOptions,
  GetPreferencesFnResp,
  PrivacyExperience,
} from "../../lib/consent-types";
import { debugLog } from "../../lib/consent-utils";
import { CookieKeyConsent } from "../../lib/cookie";

/**
 * Helper function to get preferences from an external API
 */
export async function customGetConsentPreferences(
  config: FidesConfig
): Promise<GetPreferencesFnResp | null> {
  if (!config.options.apiOptions?.getPreferencesFn) {
    return null;
  }
  debugLog(config.options.debug, "Calling custom get preferences fn");
  try {
    return await config.options.apiOptions.getPreferencesFn(config);
  } catch (e) {
    debugLog(
      config.options.debug,
      "Error retrieving preferences from custom API, continuing. Error: ",
      e
    );
    return null;
  }
}

/**
 * Helper function to save preferences to an external API
 */
export async function customSaveConsentPreferences(
  options: FidesOptions,
  consent: CookieKeyConsent,
  experience: PrivacyExperience,
  fides_string?: string
): Promise<void> {
  if (!options.apiOptions?.savePreferencesFn) {
    return;
  }
  debugLog(options.debug, "Calling custom save preferences fn");
  try {
    await options.apiOptions.savePreferencesFn(
      consent,
      fides_string,
      experience
    );
  } catch (e) {
    debugLog(
      options.debug,
      "Error saving preferences to custom API, continuing. Error: ",
      e
    );
  }
}
