import type {
  CookieKeyConsent,
  FidesCookie,
  FidesOptions,
  PrivacyExperience,
} from "../lib/consent-types";

/**
 * The type of the parent component for the preact app
 *
 * When using fides.ts to render the preact app, need to use this type!
 * Similarly, when creating different overlay "types", they should all take
 * this type as a prop.
 */
export interface OverlayProps {
  options: FidesOptions;
  experience: PrivacyExperience;
  cookie: FidesCookie;
  fidesRegionString: string;
  savedConsent?: CookieKeyConsent;
}
