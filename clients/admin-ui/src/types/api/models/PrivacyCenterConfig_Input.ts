/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__privacy_center_config__ConsentConfig_Input } from "./fides__api__schemas__privacy_center_config__ConsentConfig_Input";
import type { PrivacyRequestOption_Input } from "./PrivacyRequestOption_Input";

/**
 * NOTE: Add to this schema with care. Any fields added to
 * this response schema will be exposed in public-facing
 * (i.e. unauthenticated) API responses. If a field has
 * sensitive information, it should NOT be added to this schema!
 */
export type PrivacyCenterConfig_Input = {
  title: string;
  description: string;
  description_subtext?: Array<string> | null;
  addendum?: Array<string> | null;
  server_url_development?: string | null;
  server_url_production?: string | null;
  logo_path?: string | null;
  logo_url?: string | null;
  favicon_path?: string | null;
  actions: Array<PrivacyRequestOption_Input>;
  includeConsent?: boolean | null;
  consent: fides__api__schemas__privacy_center_config__ConsentConfig_Input;
  privacy_policy_url?: string | null;
  privacy_policy_url_text?: string | null;
};
