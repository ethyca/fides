/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ContactDetails } from "./ContactDetails";
import type { Cookie } from "./Cookie";
import type { DataFlow } from "./DataFlow";
import type { DataProtectionImpactAssessment } from "./DataProtectionImpactAssessment";
import type { DataResponsibilityTitle } from "./DataResponsibilityTitle";
import type { LegalBasisForProfilingEnum } from "./LegalBasisForProfilingEnum";
import type { PrivacyDeclaration } from "./PrivacyDeclaration";
import type { SystemMetadata } from "./SystemMetadata";

/**
 * A Compass vendor record, extending a fideslang `System`
 */
export type Vendor = {
  fides_key?: string;
  /**
   * Defines the Organization that this resource belongs to.
   */
  organization_fides_key?: string;
  tags?: Array<string>;
  name?: string;
  /**
   * A detailed description of what this resource is.
   */
  description?: string;
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
  system_type?: string;
  /**
   * The resources to which the system sends data.
   */
  egress?: Array<DataFlow>;
  /**
   * The resources from which the system receives data.
   */
  ingress?: Array<DataFlow>;
  privacy_declarations?: Array<PrivacyDeclaration>;
  /**
   * An optional value to identify the owning department or group of the system within your organization
   */
  administrating_department?: string;
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
   * The record's GVL purposes
   */
  purposes?: Array<number>;
  /**
   * The record's GVL special purposes
   */
  special_purposes?: Array<number>;
  /**
   * The record's GVL legitimate interest purposes
   */
  leg_int_purposes?: Array<number>;
  /**
   * The record's GVL flexible purposes
   */
  flexible_purposes?: Array<number>;
  /**
   * The record's GVL features
   */
  features?: Array<number>;
  /**
   * The record's GVL special features
   */
  special_features?: Array<number>;
  /**
   * The vendor's GVL-provided data declaration list, which forms the basis for its associated data categories
   */
  data_declaration?: Array<number>;
  /**
   * The vendor's GVL-provided device storage disclosure URL
   */
  device_storage_disclosure_url?: string;
  /**
   * The vendor's GVL-provided `overflow` property
   */
  overflow?: string;
  /**
   * The vendor's territorial scope list, provided by the GVL additional information list
   */
  territorial_scope?: Array<string>;
  /**
   * The vendor's environments, provided by the GVL additional information list
   */
  environments?: Array<string>;
  /**
   * The vendor's service types, provided by the GVL additional information list
   */
  service_types?: Array<string>;
  /**
   * The vendor's domains, as provided by the Google additional consent providers list.
   */
  domains?: string;
  /**
   * The URL pointing to the vendor's logo
   */
  logo?: string;
  /**
   * The version of GVL from which the record is derived
   */
  gvl_version?: string;
  /**
   * The Cookies associated with the record
   */
  cookies?: Array<Cookie>;
};
