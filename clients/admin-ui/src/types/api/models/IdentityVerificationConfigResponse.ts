/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response for identity verification config info
 */
export type IdentityVerificationConfigResponse = {
  identity_verification_required: boolean;
  disable_consent_identity_verification: boolean;
  valid_email_config_exists: boolean;
};
