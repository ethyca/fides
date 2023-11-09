import {
  EmptyExperience,
  FidesOptions,
  PrivacyExperience,
} from "../../lib/consent-types";
import { debugLog } from "../../lib/consent-utils";

/**
 * Helper function to get experience from an external API
 */
export async function customGetPrivacyExperience(
  options: FidesOptions,
  userLocationString: string,
  fidesUserDeviceId?: string | null
): Promise<PrivacyExperience | EmptyExperience | undefined> {
  if (!options.apiOptions?.getPrivacyExperienceFn) {
    return;
  }
  debugLog(options.debug, "Calling fetch experience fn");
  try {
    // eslint-disable-next-line consistent-return
    return await options.apiOptions.getPrivacyExperienceFn(
      userLocationString,
      fidesUserDeviceId
    );
  } catch (e) {
    debugLog(
      options.debug,
      "Error fetching experience from custom API, continuing. Error: ",
      e
    );
  }
}
