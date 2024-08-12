/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ProviderEnum } from "./ProviderEnum";

/**
 * Base for OpenIDProvider API objects
 */
export type OpenIDProviderRead = {
  identifier: string;
  name: string;
  provider: ProviderEnum;
  client_id: string;
  client_secret: string;
  authorization_url?: string;
  token_url?: string;
  user_info_url?: string;
  domain?: string;
  id: string;
  created_at: string;
  updated_at: string;
};
