/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Identity } from "./Identity";
import type { ServingComponent } from "./ServingComponent";

/**
 * Request body to use when saving that consent was served
 */
export type RecordConsentServedRequest = {
  browser_identity: Identity;
  code?: string;
  privacy_notice_history_ids?: Array<string>;
  tcf_purposes?: Array<number>;
  tcf_special_purposes?: Array<number>;
  tcf_vendors?: Array<string>;
  tcf_features?: Array<number>;
  tcf_special_features?: Array<number>;
  tcf_systems?: Array<string>;
  privacy_experience_id?: string;
  user_geography?: string;
  acknowledge_mode?: boolean;
  serving_component: ServingComponent;
};
