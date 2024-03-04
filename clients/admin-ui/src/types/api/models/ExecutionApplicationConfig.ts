/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type ExecutionApplicationConfig = {
  subject_identity_verification_required?: boolean;
  disable_consent_identity_verification?: boolean;
  require_manual_request_approval?: boolean;
};

