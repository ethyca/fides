/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ContactDetails } from "./ContactDetails";
import type { DataFlow } from "./DataFlow";
import type { DataProtectionImpactAssessment } from "./DataProtectionImpactAssessment";
import type { DataResponsibilityTitle } from "./DataResponsibilityTitle";
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
   * An optional property to store any extra information for a system. Not used by fidesctl.
   */
  meta?: Record<string, string>;
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
   *
   * The model defining the responsibility or role over
   * the system that processes personal data.
   *
   * Used to identify whether the organization is a
   * Controller, Processor, or Sub-Processor of the data
   *
   */
  data_responsibility_title?: DataResponsibilityTitle;
  /**
   * The resources to which the System sends data.
   */
  egress?: Array<DataFlow>;
  /**
   * The resources from which the System receives data.
   */
  ingress?: Array<DataFlow>;
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
   *
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
   * An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in ISO 3166-1.
   */
  third_country_transfers?: Array<string>;
  /**
   * An optional value to identify the owning department or group of the system within your organization
   */
  administrating_department?: string;
  /**
   *
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
};
