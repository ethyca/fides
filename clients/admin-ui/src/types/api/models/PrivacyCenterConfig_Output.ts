/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__privacy_center_config__ConsentConfig_Output } from "./fides__api__schemas__privacy_center_config__ConsentConfig_Output";
import type { PrivacyRequestOption_Output } from "./PrivacyRequestOption_Output";

/**
 * NOTE: Add to this schema with care. Any fields added to
 * this response schema will be exposed in public-facing
 * (i.e. unauthenticated) API responses. If a field has
 * sensitive information, it should NOT be added to this schema!
 */
export type PrivacyCenterConfig_Output = {
  title: string;
  description: string;
  description_subtext?: Array<string> | null;
  addendum?: Array<string> | null;
  server_url_development?: string | null;
  server_url_production?: string | null;
  logo_path?: string | null;
  logo_url?: string | null;
  favicon_path?: string | null;
  actions: Array<PrivacyRequestOption_Output>;
  includeConsent?: boolean | null;
  consent: fides__api__schemas__privacy_center_config__ConsentConfig_Output;
  privacy_policy_url?: string | null;
  privacy_policy_url_text?: string | null;
};
