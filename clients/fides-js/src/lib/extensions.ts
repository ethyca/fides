import type {
  EmptyExperience,
  FidesOptions,
  PrivacyExperience,
} from "./consent-types";

export const setupExtensions = async ({
  options,
  experience,
}: {
  options: FidesOptions;
  experience: PrivacyExperience | EmptyExperience | undefined;
}) => {
  if (experience?.gpp_settings?.enabled) {
    try {
      await import(`${options.fidesJsBaseUrl}/fides-ext-gpp.js`);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error("Unable to import GPP extension", e);
    }
  }
};
