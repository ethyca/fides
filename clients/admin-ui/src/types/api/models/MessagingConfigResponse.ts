/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MessagingServiceType } from "./MessagingServiceType";

/**
 * Messaging Config Response Schema
 */
export type MessagingConfigResponse = {
  name: string;
  key: string;
  service_type: MessagingServiceType;
  details?: any;
};
