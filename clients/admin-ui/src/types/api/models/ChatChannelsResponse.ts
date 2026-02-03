/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SlackChannel } from "./SlackChannel";

/**
 * Response schema for list of available channels.
 */
export type ChatChannelsResponse = {
  channels: Array<SlackChannel>;
};
