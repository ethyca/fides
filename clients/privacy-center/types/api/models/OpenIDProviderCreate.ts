/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ProviderEnum } from './ProviderEnum';

/**
 * Schema for creating an OpenIDProvider, including sensitive values client ID and secret.
 */
export type OpenIDProviderCreate = {
  identifier: string;
  name: string;
  provider: ProviderEnum;
  authorization_url?: string;
  token_url?: string;
  user_info_url?: string;
  domain?: string;
  client_id: string;
  client_secret: string;
};

