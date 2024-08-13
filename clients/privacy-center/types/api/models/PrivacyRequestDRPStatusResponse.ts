/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyRequestDRPStatus } from "./PrivacyRequestDRPStatus";

/**
 * A Fidesops PrivacyRequest updated to fit the Data Rights Protocol specification.
 */
export type PrivacyRequestDRPStatusResponse = {
  request_id: string;
  received_at: string;
  expected_by?: string;
  processing_details?: string;
  status: PrivacyRequestDRPStatus;
  reason?: string;
  user_verification_url?: string;
};
