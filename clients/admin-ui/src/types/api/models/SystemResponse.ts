/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionConfigurationResponse } from "./ConnectionConfigurationResponse";
import type { ContactDetails } from "./ContactDetails";
import type { Cookies } from "./Cookies";
import type { DataFlow } from "./DataFlow";
import type { DataProtectionImpactAssessment } from "./DataProtectionImpactAssessment";
import type { DataResponsibilityTitle } from "./DataResponsibilityTitle";
import type { LegalBasisForProfilingEnum } from "./LegalBasisForProfilingEnum";
import type { PrivacyDeclarationResponse } from "./PrivacyDeclarationResponse";
import type { SystemMetadata } from "./SystemMetadata";
import type { UserResponse } from "./UserResponse";

/**
 * Extension of base pydantic response model to include additional relationship fields that
 * may require extra DB queries, like `privacy_declarations`, connection_config fields and cookies.
 *
 * This response model is generally useful for an API that returns a detailed view of _single_
 * System record. Attempting to return bulk results with this model can lead to n+1 query issues.
 */
export type SystemResponse = {
  /**
   * A unique key used to identify this resource.
   */
  fides_key: string;
  /**
   * Defines the Organization that this resource belongs to.
   */
  organization_fides_key?: string;
  tags?: Array<string>;
  /**
   * Human-Readable name for this resource.
   */
  name?: string;
  /**
   * A detailed description of what this resource is.
   */
  description?: string;
  /**
   * The id of the system registry, if used.
   */
  registry_id?: number;
  /**
   * An optional property to store any extra information for a resource. Data can be structured in any way: simple set of `key: value` pairs or deeply nested objects.
   */
  meta?: any;
  /**
   *
   * The SystemMetadata resource model.
   *
   * Object used to hold application specific metadata for a system
   *
   */
  fidesctl_meta?: SystemMetadata;
  /**
   * A required value to describe the type of system being modeled, examples include: Service, Application, Third Party, etc.
   */
  system_type: string;
  /**
   * Deprecated. The responsibility or role over the system that processes personal data
   */
  data_responsibility_title?: DataResponsibilityTitle;
  /**
   * The resources to which the system sends data.
   */
  egress?: Array<DataFlow>;
  /**
   * The resources from which the system receives data.
   */
  ingress?: Array<DataFlow>;
  /**
   * Extension of base pydantic model to include DB `id` field in the response
   */
  privacy_declarations: Array<PrivacyDeclarationResponse>;
  /**
   * Deprecated.
   * The contact details information model.
   *
   * Used to capture contact information for controllers, used
   * as part of exporting a data map / ROPA.
   *
   * This model is nested under an Organization and
   * potentially under a system/dataset.
   *
   */
  joint_controller?: ContactDetails;
  /**
   * Deprecated. An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in ISO 3166-1.
   */
  third_country_transfers?: Array<string>;
  /**
   * An optional value to identify the owning department or group of the system within your organization
   */
  administrating_department?: string;
  /**
   * Deprecated.
   * The DataProtectionImpactAssessment (DPIA) resource model.
   *
   * Contains information in regard to the data protection
   * impact assessment exported on a data map or Record of
   * Processing Activities (RoPA).
   *
   * A legal requirement under GDPR for any project that
   * introduces a high risk to personal information.
   *
   */
  data_protection_impact_assessment?: DataProtectionImpactAssessment;
  /**
   * The unique identifier for the vendor that's associated with this system.
   */
  vendor_id?: string;
  /**
   * Referenced Dataset fides keys used by the system.
   */
  dataset_references?: Array<string>;
  /**
   * This toggle indicates whether the system stores or processes personal data.
   */
  processes_personal_data?: boolean;
  /**
   * This toggle indicates whether the system is exempt from privacy regulation if they do process personal data.
   */
  exempt_from_privacy_regulations?: boolean;
  /**
   * The reason that the system is exempt from privacy regulation.
   */
  reason_for_exemption?: string;
  /**
   * Whether the vendor uses data to profile a consumer in a way that has a legal effect.
   */
  uses_profiling?: boolean;
  /**
   * The legal basis (or bases) for performing profiling that has a legal effect.
   */
  legal_basis_for_profiling?: Array<LegalBasisForProfilingEnum>;
  /**
   * Whether this system transfers data to other countries or international organizations.
   */
  does_international_transfers?: boolean;
  /**
   * The legal basis (or bases) under which the data is transferred.
   */
  legal_basis_for_transfers?: Array<string>;
  /**
   * Whether this system requires data protection impact assessments.
   */
  requires_data_protection_assessments?: boolean;
  /**
   * Location where the DPAs or DIPAs can be found.
   */
  dpa_location?: string;
  /**
   * The optional status of a Data Protection Impact Assessment
   */
  dpa_progress?: string;
  /**
   * A URL that points to the system's publicly accessible privacy policy.
   */
  privacy_policy?: string;
  /**
   * The legal name for the business represented by the system.
   */
  legal_name?: string;
  /**
   * The legal address for the business represented by the system.
   */
  legal_address?: string;
  /**
   *
   * The model defining the responsibility or role over
   * the system that processes personal data.
   *
   * Used to identify whether the organization is a
   * Controller, Processor, or Sub-Processor of the data
   *
   */
  responsibility?: Array<DataResponsibilityTitle>;
  /**
   * The official privacy contact address or DPO.
   */
  dpo?: string;
  /**
   * The party or parties that share the responsibility for processing personal data.
   */
  joint_controller_info?: string;
  /**
   * The data security practices employed by this system.
   */
  data_security_practices?: string;
  /**
   * The maximum storage duration, in seconds, for cookies used by this system.
   */
  cookie_max_age_seconds?: number;
  /**
   * Whether this system uses cookie storage.
   */
  uses_cookies?: boolean;
  /**
   * Whether the system's cookies are refreshed after being initially set.
   */
  cookie_refresh?: boolean;
  /**
   * Whether the system uses non-cookie methods of storage or accessing information stored on a user's device.
   */
  uses_non_cookie_access?: boolean;
  /**
   * A URL that points to the system's publicly accessible legitimate interest disclosure.
   */
  legitimate_interest_disclosure_url?: string;
  /**
   * System-level cookies unassociated with a data use to deliver services and functionality
   */
  cookies?: Array<Cookies>;
  created_at: string;
  /**
   *
   * Describes the returned schema for a ConnectionConfiguration.
   *
   */
  connection_configs?: ConnectionConfigurationResponse;
  /**
   * System managers of the current system
   */
  data_stewards?: Array<UserResponse>;
};
