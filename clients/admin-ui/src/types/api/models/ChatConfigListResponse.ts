/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ChatProviderSettingsResponse } from "./ChatProviderSettingsResponse";

/**
 * Response schema for list of chat configurations.
 */
export type ChatConfigListResponse = {
  items: Array<ChatProviderSettingsResponse>;
  total: number;
};
