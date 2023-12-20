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
      await import(options.gppExtensionPath);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error("Unable to import GPP extension", e);
    }
  }
};
