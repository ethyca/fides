/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { OAuthGrantType } from "./OAuthGrantType";

/**
 * Schema for OAuth2 configuration used in API requests
 */
export type OAuthConfigSchema = {
  grant_type?: OAuthGrantType | null;
  token_url?: string | null;
  scope?: string | null;
  client_id?: string | null;
  client_secret: string | null;
};
