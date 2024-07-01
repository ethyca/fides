/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BasicMessagingTemplateResponse } from "./BasicMessagingTemplateResponse";
import type { BulkUpdateFailed } from "./BulkUpdateFailed";

/**
 * Schema for responses from bulk update/create requests.  Override to set "succeeded" and "failed" attributes on
 * your child class with paginated types.
 *
 * Example:
 * from fastapi_pagination import Page
 *
 * succeeded: List[ConnectionConfigurationResponse]
 * failed: List[BulkUpdateFailed]
 */
export type BulkPutBasicMessagingTemplateResponse = {
  succeeded: Array<BasicMessagingTemplateResponse>;
  failed: Array<BulkUpdateFailed>;
};
