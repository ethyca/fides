/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MessagingServiceDetailsAWS_SES } from "./MessagingServiceDetailsAWS_SES";
import type { MessagingServiceDetailsMailchimpTransactional } from "./MessagingServiceDetailsMailchimpTransactional";
import type { MessagingServiceDetailsMailgun } from "./MessagingServiceDetailsMailgun";
import type { MessagingServiceDetailsTwilioEmail } from "./MessagingServiceDetailsTwilioEmail";
import type { MessagingServiceType } from "./MessagingServiceType";

/**
 * Messaging Config Request Schema
 */
export type MessagingConfigRequest = {
  service_type: MessagingServiceType;
  details?:
    | MessagingServiceDetailsMailgun
    | MessagingServiceDetailsTwilioEmail
    | MessagingServiceDetailsMailchimpTransactional
    | MessagingServiceDetailsAWS_SES
    | null;
  name: string;
  key?: string | null;
};
