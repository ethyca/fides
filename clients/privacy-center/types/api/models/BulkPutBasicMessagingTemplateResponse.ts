/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BasicMessagingTemplateResponse } from "./BasicMessagingTemplateResponse";
import type { BulkUpdateFailed } from "./BulkUpdateFailed";

export type BulkPutBasicMessagingTemplateResponse = {
  succeeded: Array<BasicMessagingTemplateResponse>;
  failed: Array<BulkUpdateFailed>;
};
