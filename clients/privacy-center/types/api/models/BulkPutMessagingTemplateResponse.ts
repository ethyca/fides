/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";
import type { MessagingTemplateResponse } from "./MessagingTemplateResponse";

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
export type BulkPutMessagingTemplateResponse = {
  succeeded: Array<MessagingTemplateResponse>;
  failed: Array<BulkUpdateFailed>;
};
