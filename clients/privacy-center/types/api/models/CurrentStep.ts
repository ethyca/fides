/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export enum CurrentStep {
  PRE_WEBHOOKS = "pre_webhooks",
  ACCESS = "access",
  UPLOAD_ACCESS = "upload_access",
  ERASURE = "erasure",
  FINALIZE_ERASURE = "finalize_erasure",
  CONSENT = "consent",
  FINALIZE_CONSENT = "finalize_consent",
  EMAIL_POST_SEND = "email_post_send",
  POST_WEBHOOKS = "post_webhooks",
}
