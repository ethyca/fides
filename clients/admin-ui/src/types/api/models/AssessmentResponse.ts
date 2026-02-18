/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for privacy assessments in list views.
 */
export type AssessmentResponse = {
  id: string;
  template_id: string;
  template_name?: string | null;
  name: string;
  status: string;
  completeness?: number;
  risk_level?: string | null;
  system_fides_key?: string | null;
  system_name?: string | null;
  declaration_id?: string | null;
  declaration_name?: string | null;
  data_use?: string | null;
  data_use_name?: string | null;
  data_categories?: Array<string>;
  created_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};
