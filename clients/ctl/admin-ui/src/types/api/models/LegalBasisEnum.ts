/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for allowable legal basis categories
 *
 * Based upon article 6 of the GDPR
 */
export enum LegalBasisEnum {
  CONSENT = 'Consent',
  CONTRACT = 'Contract',
  LEGAL_OBLIGATION = 'Legal Obligation',
  VITAL_INTEREST = 'Vital Interest',
  PUBLIC_INTEREST = 'Public Interest',
  LEGITIMATE_INTERESTS = 'Legitimate Interests',
}