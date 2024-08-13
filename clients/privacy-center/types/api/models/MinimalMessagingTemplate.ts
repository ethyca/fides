/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Minimal representation of a messaging template.
 *
 * NOTE: Add to this schema with care. Any fields added to
 * this response schema will be exposed in public-facing
 * (i.e. unauthenticated) API responses. If a field has
 * sensitive information, it should NOT be added to this schema!
 */
export type MinimalMessagingTemplate = {
  id: string;
  type: string;
};
