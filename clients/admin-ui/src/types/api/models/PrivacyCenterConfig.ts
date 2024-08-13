/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__privacy_center_config__ConsentConfig } from './fides__api__schemas__privacy_center_config__ConsentConfig';
import type { PrivacyRequestOption } from './PrivacyRequestOption';

/**
 * NOTE: Add to this schema with care. Any fields added to
 * this response schema will be exposed in public-facing
 * (i.e. unauthenticated) API responses. If a field has
 * sensitive information, it should NOT be added to this schema!
 */
export type PrivacyCenterConfig = {
  title: string;
  description: string;
  description_subtext?: Array<string>;
  addendum?: Array<string>;
  server_url_development?: string;
  server_url_production?: string;
  logo_path?: string;
  logo_url?: string;
  favicon_path?: string;
  actions: Array<PrivacyRequestOption>;
  includeConsent?: boolean;
  consent: fides__api__schemas__privacy_center_config__ConsentConfig;
  privacy_policy_url?: string;
  privacy_policy_url_text?: string;
};

