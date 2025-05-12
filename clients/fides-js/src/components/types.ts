import type {
  FidesCookie,
  FidesExperienceTranslationOverrides,
  FidesInitOptions,
  NoticeConsent,
  PrivacyExperience,
} from "../lib/consent-types";
import type { I18n } from "../lib/i18n";

/**
 * The type of the parent component for the preact app
 *
 * When using fides.ts to render the preact app, need to use this type!
 * Similarly, when creating different overlay "types", they should all take
 * this type as a prop.
 */
export interface OverlayProps {
  options: FidesInitOptions;
  experience: PrivacyExperience;
  i18n: I18n;
  cookie: FidesCookie;
  fidesRegionString: string;
  savedConsent: NoticeConsent;
  propertyId?: string;
  translationOverrides?: Partial<FidesExperienceTranslationOverrides>;
}
