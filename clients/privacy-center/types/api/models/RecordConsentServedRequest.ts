/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Identity } from "./Identity";
import type { ServingComponent } from "./ServingComponent";

/**
 * Request body to use when saving that consent was served
 */
export type RecordConsentServedRequest = {
  tcf_purpose_consents?: Array<number>;
  tcf_purpose_legitimate_interests?: Array<number>;
  tcf_special_purposes?: Array<number>;
  tcf_vendor_consents?: Array<string>;
  tcf_vendor_legitimate_interests?: Array<string>;
  tcf_features?: Array<number>;
  tcf_special_features?: Array<number>;
  tcf_system_consents?: Array<string>;
  tcf_system_legitimate_interests?: Array<string>;
  privacy_notice_history_ids?: Array<string>;
  browser_identity: Identity;
  code?: string | null;
  privacy_experience_id?: string | null;
  privacy_experience_config_history_id?: string | null;
  user_geography?: string | null;
  acknowledge_mode?: boolean | null;
  served_notice_history_id?: string | null;
  serving_component: ServingComponent;
  property_id?: string | null;
};
