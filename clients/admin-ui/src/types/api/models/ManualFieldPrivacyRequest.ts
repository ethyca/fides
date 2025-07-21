/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ManualFieldRequestType } from "./ManualFieldRequestType";

/**
 * Privacy request snapshot with identity fields.
 */
export type ManualFieldPrivacyRequest = {
  id: string;
  /**
   * Days remaining until due date
   */
  days_left?: number | null;
  request_type: ManualFieldRequestType;
  subject_identities: any;
  custom_fields: any;
};
