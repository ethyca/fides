import * as Yup from "yup";

import {
  ConsentMechanism,
  EnforcementLevel,
  PrivacyNoticeCreation,
  PrivacyNoticeResponse,
} from "~/types/api";

interface PrivacyNoticeUpdateOrCreate extends PrivacyNoticeCreation {
  id?: string;
}

export const defaultInitialValues: PrivacyNoticeUpdateOrCreate = {
  name: "",
  consent_mechanism: ConsentMechanism.OPT_IN,
  data_uses: [],
  enforcement_level: EnforcementLevel.SYSTEM_WIDE,
  // When creating, set to disabled to start
  disabled: true,
};

export const transformPrivacyNoticeResponseToCreation = (
  notice: PrivacyNoticeResponse
): PrivacyNoticeUpdateOrCreate => ({
  name: notice.name ?? defaultInitialValues.name,
  consent_mechanism:
    notice.consent_mechanism ?? defaultInitialValues.consent_mechanism,
  data_uses: notice.data_uses ?? defaultInitialValues.data_uses,
  enforcement_level:
    notice.enforcement_level ?? defaultInitialValues.enforcement_level,
  notice_key: notice.notice_key,
  disabled: notice.disabled,
  has_gpc_flag: notice.has_gpc_flag,
  id: notice.id,
  internal_description: notice.internal_description,
});

export const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Title"),
});
