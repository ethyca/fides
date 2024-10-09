/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ProviderEnum } from "./ProviderEnum";

/**
 * Schema for creating an OpenIDProvider, including sensitive values client ID and secret.
 */
export type OpenIDProviderCreate = {
  identifier: string;
  name: string;
  provider: ProviderEnum;
  authorization_url?: string | null;
  token_url?: string | null;
  user_info_url?: string | null;
  domain?: string | null;
  client_id: string;
  client_secret: string;
};
