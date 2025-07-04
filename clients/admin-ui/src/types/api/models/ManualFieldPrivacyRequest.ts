/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fidesplus__api__schemas__manual_task__manual_task_search__CustomPrivacyRequestField } from "./fidesplus__api__schemas__manual_task__manual_task_search__CustomPrivacyRequestField";
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
  custom_fields: Array<fidesplus__api__schemas__manual_task__manual_task_search__CustomPrivacyRequestField>;
};
