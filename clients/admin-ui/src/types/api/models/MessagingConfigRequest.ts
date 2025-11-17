/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MessagingSecretsMailgunDocs } from "./MessagingSecretsMailgunDocs";
import type { MessagingSecretsTwilioEmailDocs } from "./MessagingSecretsTwilioEmailDocs";
import type { MessagingSecretsTwilioSMSDocs } from "./MessagingSecretsTwilioSMSDocs";
import type { MessagingServiceDetailsAWS_SES } from "./MessagingServiceDetailsAWS_SES";
import type { MessagingServiceDetailsMailchimpTransactional } from "./MessagingServiceDetailsMailchimpTransactional";
import type { MessagingServiceDetailsMailgun } from "./MessagingServiceDetailsMailgun";
import type { MessagingServiceDetailsTwilioEmail } from "./MessagingServiceDetailsTwilioEmail";
import type { MessagingServiceSecretsAWS_SESDocs } from "./MessagingServiceSecretsAWS_SESDocs";
import type { MessagingServiceSecretsMailchimpTransactionalDocs } from "./MessagingServiceSecretsMailchimpTransactionalDocs";
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
  name?: string | null;
  key?: string | null;
  secrets?:
    | MessagingSecretsMailgunDocs
    | MessagingSecretsTwilioSMSDocs
    | MessagingSecretsTwilioEmailDocs
    | MessagingServiceSecretsMailchimpTransactionalDocs
    | MessagingServiceSecretsAWS_SESDocs
    | null;
};
