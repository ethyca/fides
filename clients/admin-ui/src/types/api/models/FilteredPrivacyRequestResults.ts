/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyRequestStatus } from "./PrivacyRequestStatus";

/**
 * Schema representing the status and results of a test privacy request
 */
export type FilteredPrivacyRequestResults = {
  privacy_request_id: string;
  status: PrivacyRequestStatus;
  results: string;
};
