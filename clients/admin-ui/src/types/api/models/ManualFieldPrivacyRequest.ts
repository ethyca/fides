/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ManualFieldRequestType } from "./ManualFieldRequestType";
import type { SubjectIdentitySnapshot } from "./SubjectIdentitySnapshot";

export type ManualFieldPrivacyRequest = {
  id: string;
  /**
   * Days remaining until due date
   */
  days_left?: number | null;
  request_type: ManualFieldRequestType;
  subject_identity?: SubjectIdentitySnapshot | null;
};
