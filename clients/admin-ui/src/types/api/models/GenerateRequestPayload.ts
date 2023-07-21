/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Generate } from "./Generate";

/**
 * The model for the request body housing generate information.
 */
export type GenerateRequestPayload = {
  organization_key: string;
  generate: Generate;
};
