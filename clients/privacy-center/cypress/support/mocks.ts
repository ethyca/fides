import {
  PrivacyNotice,
  EnforcementLevel,
  ConsentMechanism,
  UserConsentPreference,
} from "fides-js";

export const mockPrivacyNotice = (params: Partial<PrivacyNotice>) => {
  const notice = {
    name: "Test privacy notice with GPC enabled",
    disabled: false,
    origin: "12435134",
    description: "a test sample privacy notice configuration",
    internal_description:
      "a test sample privacy notice configuration for internal use",
    regions: ["us_ca"],
    consent_mechanism: ConsentMechanism.OPT_OUT,
    default_preference: UserConsentPreference.OPT_IN,
    current_preference: undefined,
    outdated_preference: undefined,
    has_gpc_flag: true,
    data_uses: ["advertising", "third_party_sharing"],
    enforcement_level: EnforcementLevel.SYSTEM_WIDE,
    displayed_in_overlay: true,
    displayed_in_api: true,
    displayed_in_privacy_center: false,
    id: "pri_4bed96d0-b9e3-4596-a807-26b783836374",
    created_at: "2023-04-24T21:29:08.870351+00:00",
    updated_at: "2023-04-24T21:29:08.870351+00:00",
    version: 1.0,
    privacy_notice_history_id: "pri_b09058a7-9f54-4360-8da5-4521e8975d4f",
    notice_key: "advertising",
    cookies: [],
  };
  return { ...notice, ...params };
};
