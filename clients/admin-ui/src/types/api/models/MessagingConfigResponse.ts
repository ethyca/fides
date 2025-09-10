/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MessagingServiceDetailsAWS_SES } from "./MessagingServiceDetailsAWS_SES";
import type { MessagingServiceDetailsMailchimpTransactional } from "./MessagingServiceDetailsMailchimpTransactional";
import type { MessagingServiceDetailsMailgun } from "./MessagingServiceDetailsMailgun";
import type { MessagingServiceDetailsTwilioEmail } from "./MessagingServiceDetailsTwilioEmail";
import type { MessagingServiceType } from "./MessagingServiceType";

/**
 * Messaging Config Response Schema
 */
export type MessagingConfigResponse = {
  service_type: MessagingServiceType;
  details?:
    | MessagingServiceDetailsMailgun
    | MessagingServiceDetailsTwilioEmail
    | MessagingServiceDetailsMailchimpTransactional
    | MessagingServiceDetailsAWS_SES
    | null;
  name: string;
  last_test_timestamp: string;
  last_test_succeeded: boolean;
  key: string;
};
