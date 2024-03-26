import type {
  EmptyExperience,
  FidesOptions,
  PrivacyExperience,
} from "./consent-types";
import { debugLog } from "./consent-utils";

export const setupExtensions = async ({
  options,
  experience,
}: {
  options: FidesOptions;
  experience: PrivacyExperience | EmptyExperience | undefined;
}) => {
  // TODO (PROD-1830): pre-bundle this when GPP is enabled instead of relying on experience
  if (experience?.gpp_settings?.enabled) {
    try {
      await import(`${options.fidesJsBaseUrl}/fides-ext-gpp.js`);
      debugLog(options.debug, "Imported & executed GPP extension");
    } catch (e) {
      debugLog(options.debug, "Unable to import GPP extension");
    }
  }
};
