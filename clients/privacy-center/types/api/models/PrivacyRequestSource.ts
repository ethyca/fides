/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The source where the privacy request originated from
 *
 * - Privacy Center: Request created from the Privacy Center
 * - Request Manager: Request submitted from the Admin UI's Request manager page
 * - Consent Webhook: Request created as a side-effect of a consent webhook request (bidirectional consent)
 * - Fides.js: Request created as a side-effect of a privacy preference update from Fides.js
 */
export enum PrivacyRequestSource {
  PRIVACY_CENTER = "Privacy Center",
  REQUEST_MANAGER = "Request Manager",
  CONSENT_WEBHOOK = "Consent Webhook",
  FIDES_JS = "Fides.js",
}
