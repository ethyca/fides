import { FidesConfig, GetPreferencesFnResp } from "../../lib/consent-types";

/**
 * Helper function to get preferences from an external API
 */
export async function customGetConsentPreferences(
  config: FidesConfig,
): Promise<GetPreferencesFnResp | null> {
  if (!config.options.apiOptions?.getPreferencesFn) {
    return null;
  }
  fidesDebugger("Calling custom get preferences fn");
  try {
    return await config.options.apiOptions.getPreferencesFn(config);
  } catch (e) {
    fidesDebugger(
      "Error retrieving preferences from custom API, continuing. Error: ",
      e,
    );
    return null;
  }
}
