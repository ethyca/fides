/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Authentication protocol types supported by identity providers.
 */
export enum AuthenticationProtocol {
  SAML_2_0 = "SAML_2_0",
  OPENID_CONNECT = "OPENID_CONNECT",
  WS_FEDERATION = "WS_FEDERATION",
  OAUTH_2_0 = "OAUTH_2_0",
  BROWSER_PLUGIN = "BROWSER_PLUGIN",
  CUSTOM = "CUSTOM",
}
