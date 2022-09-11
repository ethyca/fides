/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for processing special categories
 * of personal data.
 *
 * Based upon article 9 of the GDPR
 */
export enum SpecialCategoriesEnum {
  CONSENT = 'Consent',
  EMPLOYMENT = 'Employment',
  VITAL_INTERESTS = 'Vital Interests',
  NON_PROFIT_BODIES = 'Non-profit Bodies',
  PUBLIC_BY_DATA_SUBJECT = 'Public by Data Subject',
  LEGAL_CLAIMS = 'Legal Claims',
  SUBSTANTIAL_PUBLIC_INTEREST = 'Substantial Public Interest',
  MEDICAL = 'Medical',
  PUBLIC_HEALTH_INTEREST = 'Public Health Interest',
}