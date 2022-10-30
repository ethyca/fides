/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";
import type { PrivacyRequestResponse } from "./PrivacyRequestResponse";

/**
 * Schema with mixed success/failure responses for Bulk Create of PrivacyRequest responses.
 */
export type BulkPostPrivacyRequests = {
  succeeded: Array<PrivacyRequestResponse>;
  failed: Array<BulkUpdateFailed>;
};
