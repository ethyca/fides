/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ProviderEnum } from "./ProviderEnum";

/**
 * Complete schema, does NOT include sensitive values.
 */
export type OpenIDProvider = {
  identifier: string;
  name: string;
  provider: ProviderEnum;
  authorization_url?: string | null;
  token_url?: string | null;
  user_info_url?: string | null;
  domain?: string | null;
  id: string;
  created_at: string;
  updated_at: string;
};
