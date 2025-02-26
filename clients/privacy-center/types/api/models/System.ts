/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Cookies } from "./Cookies";
import type { DataFlow } from "./DataFlow";
import type { DataResponsibilityTitle } from "./DataResponsibilityTitle";
import type { LegalBasisForProfilingEnum } from "./LegalBasisForProfilingEnum";
import type { PrivacyDeclaration } from "./PrivacyDeclaration";
import type { SystemMetadata } from "./SystemMetadata";

/**
 * The System resource model.
 *
 * Describes an application and includes a list of PrivacyDeclaration resources.
 */
export type System = {
  /**
   * A unique key used to identify this resource.
   */
  fides_key: string;
  /**
   * Defines the Organization that this resource belongs to.
   */
  organization_fides_key?: string;
  tags?: Array<string> | null;
  /**
   * Human-Readable name for this resource.
   */
  name?: string | null;
  /**
   * A detailed description of what this resource is.
   */
  description?: string | null;
  /**
   * An optional property to store any extra information for a resource. Data can be structured in any way: simple set of `key: value` pairs or deeply nested objects.
   */
  meta?: null;
  /**
   *
   * The SystemMetadata resource model.
   *
   * Object used to hold application specific metadata for a system
   *
   */
  fidesctl_meta?: SystemMetadata | null;
  /**
   * A required value to describe the type of system being modeled, examples include: Service, Application, Third Party, etc.
   */
  system_type: string;
  /**
   * The resources to which the system sends data.
   */
  egress?: Array<DataFlow> | null;
  /**
   * The resources from which the system receives data.
   */
  ingress?: Array<DataFlow> | null;
  /**
   *
   * The PrivacyDeclaration resource model.
   *
   * States a function of a system, and describes how it relates
   * to the privacy data types.
   *
   */
  privacy_declarations: Array<PrivacyDeclaration>;
  /**
   * An optional value to identify the owning department or group of the system within your organization
   */
  administrating_department?: string | null;
  /**
   * The unique identifier for the vendor that's associated with this system.
   */
  vendor_id?: string | null;
  /**
   * If specified, the unique identifier for the vendor that was previously associated with this system.
   */
  previous_vendor_id?: string | null;
  /**
   * The deleted date of the vendor that's associated with this system.
   */
  vendor_deleted_date?: string | null;
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
  reason_for_exemption?: string | null;
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
  dpa_location?: string | null;
  /**
   * The optional status of a Data Protection Impact Assessment
   */
  dpa_progress?: string | null;
  /**
   * A URL that points to the system's publicly accessible privacy policy.
   */
  privacy_policy?: string | null;
  /**
   * The legal name for the business represented by the system.
   */
  legal_name?: string | null;
  /**
   * The legal address for the business represented by the system.
   */
  legal_address?: string | null;
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
  dpo?: string | null;
  /**
   * The party or parties that share the responsibility for processing personal data.
   */
  joint_controller_info?: string | null;
  /**
   * The data security practices employed by this system.
   */
  data_security_practices?: string | null;
  /**
   * The maximum storage duration, in seconds, for cookies used by this system.
   */
  cookie_max_age_seconds?: number | null;
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
  legitimate_interest_disclosure_url?: string | null;
  /**
   * System-level cookies unassociated with a data use to deliver services and functionality
   */
  cookies?: Array<Cookies> | null;
};
