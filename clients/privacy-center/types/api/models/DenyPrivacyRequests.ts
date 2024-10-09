/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Pass in a list of privacy request ids and rejection reason
 */
export type DenyPrivacyRequests = {
  request_ids: Array<string>;
  reason?: string | null;
};
