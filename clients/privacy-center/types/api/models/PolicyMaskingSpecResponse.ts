/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The schema to use when returning a masking strategy via the API. This schema omits other
 * potentially sensitive fields in the masking configuration, for example the encryption
 * algorithm.
 */
export type PolicyMaskingSpecResponse = {
  strategy: string;
};
