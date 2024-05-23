/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for the legal basis for processing special categories of personal data
 * on privacy declarations
 *
 * Based upon article 9 of the GDPR
 */
export enum SpecialCategoryLegalBasisEnum {
  EXPLICIT_CONSENT = "Explicit consent",
  EMPLOYMENT_SOCIAL_SECURITY_AND_SOCIAL_PROTECTION = "Employment, social security and social protection",
  VITAL_INTERESTS = "Vital interests",
  NOT_FOR_PROFIT_BODIES = "Not-for-profit bodies",
  MADE_PUBLIC_BY_THE_DATA_SUBJECT = "Made public by the data subject",
  LEGAL_CLAIMS_OR_JUDICIAL_ACTS = "Legal claims or judicial acts",
  REASONS_OF_SUBSTANTIAL_PUBLIC_INTEREST_WITH_A_BASIS_IN_LAW_ = "Reasons of substantial public interest (with a basis in law)",
  HEALTH_OR_SOCIAL_CARE_WITH_A_BASIS_IN_LAW_ = "Health or social care (with a basis in law)",
  PUBLIC_HEALTH_WITH_A_BASIS_IN_LAW_ = "Public health (with a basis in law)",
  ARCHIVING_RESEARCH_AND_STATISTICS_WITH_A_BASIS_IN_LAW_ = "Archiving, research and statistics (with a basis in law)",
}
