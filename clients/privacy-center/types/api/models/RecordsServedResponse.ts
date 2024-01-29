/**
 * Response when saving that consent was served
 */
export type RecordsServedResponse = {
  served_notice_history_id: string;
  privacy_notice_history_ids: string[];
  tcf_purpose_consents: number[];
  tcf_purpose_legitimate_interests: number[];
  tcf_special_purposes: number[];
  tcf_vendor_consents: string[];
  tcf_vendor_legitimate_interests: string[];
  tcf_features: number[];
  tcf_special_features: number[];
  tcf_system_consents: string[];
  tcf_system_legitimate_interests: string[];
};
