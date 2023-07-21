/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type ExecutionApplicationConfig = {
  subject_identity_verification_required?: boolean;
  require_manual_request_approval?: boolean;
};
