/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The DataProtectionImpactAssessment (DPIA) resource model.
 *
 * Contains information in regard to the data protection
 * impact assessment exported on a data map or Record of
 * Processing Activities (RoPA).
 *
 * A legal requirement under GDPR for any project that
 * introduces a high risk to personal information.
 */
export type DataProtectionImpactAssessment = {
  /**
   * A boolean value determining if a data protection impact assessment is required. Defaults to False.
   */
  is_required?: boolean;
  /**
   * The optional status of a Data Protection Impact Assessment. Returned on an exported data map or RoPA.
   */
  progress?: string;
  /**
   * The optional link to the Data Protection Impact Assessment. Returned on an exported data map or RoPA.
   */
  link?: string;
};
