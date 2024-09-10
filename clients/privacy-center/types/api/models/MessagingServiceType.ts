/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum for messaging service type. Upper-cased in the database
 */
export enum MessagingServiceType {
  MAILGUN = "mailgun",
  TWILIO_TEXT = "twilio_text",
  TWILIO_EMAIL = "twilio_email",
  MAILCHIMP_TRANSACTIONAL = "mailchimp_transactional",
}
