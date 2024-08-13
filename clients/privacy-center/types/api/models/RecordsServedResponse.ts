/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response after saving notices served (v2)
 */
export type RecordsServedResponse = {
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
  served_notice_history_id: string;
};
