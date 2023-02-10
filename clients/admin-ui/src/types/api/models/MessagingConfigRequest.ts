/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MessagingServiceDetailsMailgun } from "./MessagingServiceDetailsMailgun";
import type { MessagingServiceDetailsTwilioEmail } from "./MessagingServiceDetailsTwilioEmail";
import type { MessagingServiceType } from "./MessagingServiceType";

/**
 * Messaging Config Request Schema
 */
export type MessagingConfigRequest = {
  name: string;
  key?: string;
  service_type: MessagingServiceType;
  details?: MessagingServiceDetailsMailgun | MessagingServiceDetailsTwilioEmail;
};
