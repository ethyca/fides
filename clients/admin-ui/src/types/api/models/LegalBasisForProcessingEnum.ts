/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for allowable legal basis categories on privacy declarations.
 *
 * Based upon article 6 of the GDPR
 */
export enum LegalBasisForProcessingEnum {
  CONSENT = "Consent",
  CONTRACT = "Contract",
  LEGAL_OBLIGATIONS = "Legal obligations",
  VITAL_INTERESTS = "Vital interests",
  PUBLIC_INTEREST = "Public interest",
  LEGITIMATE_INTERESTS = "Legitimate interests",
}
