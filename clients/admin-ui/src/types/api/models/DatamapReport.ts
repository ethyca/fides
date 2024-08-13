/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type DatamapReport = {
  administrating_department?: string;
  cookie_max_age_seconds?: number;
  cookie_refresh: boolean;
  cookies?: Array<string>;
  data_categories?: string | Array<string>;
  system_undeclared_data_categories?: Array<string>;
  data_use_undeclared_data_categories?: Array<string>;
  data_security_practices?: string;
  data_shared_with_third_parties?: boolean;
  data_stewards?: Array<string>;
  data_subjects?: Array<string>;
  data_uses?: string | Array<string>;
  declaration_name?: string;
  description?: string;
  does_international_transfers: boolean;
  dpa_location?: string;
  dpo?: string;
  egress?: Array<string>;
  exempt_from_privacy_regulations: boolean;
  features?: Array<string>;
  fides_key: string;
  flexible_legal_basis_for_processing?: boolean;
  impact_assessment_location?: string;
  ingress?: Array<string>;
  joint_controller_info?: string;
  legal_address?: string;
  legal_basis_for_processing?: string;
  legal_basis_for_profiling?: Array<string>;
  legal_basis_for_transfers?: Array<string>;
  legal_name?: string;
  legitimate_interest_disclosure_url?: string;
  link_to_processor_contract?: string;
  privacy_policy?: string;
  processes_personal_data: boolean;
  reason_for_exemption?: string;
  requires_data_protection_assessments: boolean;
  responsibility?: Array<string>;
  retention_period?: string;
  shared_categories?: Array<string>;
  special_category_legal_basis?: string;
  system_dependencies?: string;
  system_name: string;
  third_country_safeguards?: string;
  third_parties?: string;
  uses_cookies: boolean;
  uses_non_cookie_access: boolean;
  uses_profiling: boolean;
};
