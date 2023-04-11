import {
  ConsentMechanism,
  EnforcementLevel,
  PrivacyNoticeCreation,
  PrivacyNoticeResponse,
} from "~/types/api";

export const defaultInitialValues: PrivacyNoticeCreation = {
  name: "",
  regions: [],
  consent_mechanism: ConsentMechanism.OPT_IN,
  data_uses: [],
  enforcement_level: EnforcementLevel.SYSTEM_WIDE,
};

export const transformPrivacyNoticeResponseToCreation = (
  notice: PrivacyNoticeResponse
): PrivacyNoticeCreation => ({
  ...notice,
  name: notice.name ?? defaultInitialValues.name,
  regions: notice.regions ?? defaultInitialValues.regions,
  consent_mechanism:
    notice.consent_mechanism ?? defaultInitialValues.consent_mechanism,
  data_uses: notice.data_uses ?? defaultInitialValues.data_uses,
  enforcement_level:
    notice.enforcement_level ?? defaultInitialValues.enforcement_level,
});
