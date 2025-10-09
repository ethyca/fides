/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DigestConfigResponse } from "./DigestConfigResponse";

/**
 * Response schema for listing digest configurations.
 */
export type DigestConfigListResponse = {
  items: Array<DigestConfigResponse>;
  total: number;
  page?: number;
  size?: number;
};
