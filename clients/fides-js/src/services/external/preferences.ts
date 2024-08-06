import { FidesConfig, GetPreferencesFnResp } from "../../lib/consent-types";
import { debugLog } from "../../lib/consent-utils";

/**
 * Helper function to get preferences from an external API
 */
export async function customGetConsentPreferences(
  config: FidesConfig,
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
      e,
    );
    return null;
  }
}
