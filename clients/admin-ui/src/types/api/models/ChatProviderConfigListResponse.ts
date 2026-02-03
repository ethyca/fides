/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ChatProviderSettingsResponse } from "./ChatProviderSettingsResponse";

/**
 * Response schema for list of chat provider configurations.
 */
export type ChatProviderConfigListResponse = {
  items: Array<ChatProviderSettingsResponse>;
  total: number;
};
