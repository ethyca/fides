/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type DatamapReport = {
  administrating_department?: string | null;
  cookie_max_age_seconds?: number | null;
  cookie_refresh: boolean;
  data_categories?: string | Array<string> | null;
  system_undeclared_data_categories?: Array<string> | null;
  data_use_undeclared_data_categories?: Array<string> | null;
  data_security_practices?: string | null;
  data_shared_with_third_parties?: boolean | null;
  data_stewards?: Array<string> | null;
  data_subjects?: Array<string> | null;
  data_uses?: string | Array<string> | null;
  declaration_name?: string | null;
  description?: string | null;
  does_international_transfers: boolean;
  dpa_location?: string | null;
  dpo?: string | null;
  egress?: Array<string> | null;
  exempt_from_privacy_regulations: boolean;
  features?: Array<string> | null;
  fides_key: string;
  flexible_legal_basis_for_processing?: boolean | null;
  impact_assessment_location?: string | null;
  ingress?: Array<string> | null;
  joint_controller_info?: string | null;
  legal_address?: string | null;
  legal_basis_for_processing?: string | null;
  legal_basis_for_profiling?: Array<string> | null;
  legal_basis_for_transfers?: Array<string> | null;
  legal_name?: string | null;
  legitimate_interest_disclosure_url?: string | null;
  privacy_policy?: string | null;
  processes_personal_data: boolean;
  reason_for_exemption?: string | null;
  requires_data_protection_assessments: boolean;
  responsibility?: Array<string> | null;
  retention_period?: string | null;
  shared_categories?: Array<string> | null;
  special_category_legal_basis?: string | null;
  system_name: string;
  third_parties?: string | null;
  uses_cookies: boolean;
  uses_non_cookie_access: boolean;
  uses_profiling: boolean;
};
