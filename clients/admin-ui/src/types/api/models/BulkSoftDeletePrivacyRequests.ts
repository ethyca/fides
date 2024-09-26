/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";

export type BulkSoftDeletePrivacyRequests = {
  succeeded: Array<string>;
  failed: Array<BulkUpdateFailed>;
};
