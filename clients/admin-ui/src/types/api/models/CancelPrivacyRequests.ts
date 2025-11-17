/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Pass in a list of privacy request ids and cancellation reason
 */
export type CancelPrivacyRequests = {
  request_ids: Array<string>;
  reason?: string | null;
};
