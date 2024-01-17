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
  regions: [],
  consent_mechanism: ConsentMechanism.OPT_IN,
  data_uses: [],
  enforcement_level: EnforcementLevel.SYSTEM_WIDE,
  // Match backend defaults
  displayed_in_api: true,
  displayed_in_overlay: true,
  displayed_in_privacy_center: true,
  // When creating, set to disabled to start
  disabled: true,
};

export const transformPrivacyNoticeResponseToCreation = (
  notice: PrivacyNoticeResponse
): PrivacyNoticeUpdateOrCreate => ({
  name: notice.name ?? defaultInitialValues.name,
  regions: notice.regions ?? defaultInitialValues.regions,
  consent_mechanism:
    notice.consent_mechanism ?? defaultInitialValues.consent_mechanism,
  data_uses: notice.data_uses ?? defaultInitialValues.data_uses,
  enforcement_level:
    notice.enforcement_level ?? defaultInitialValues.enforcement_level,
  displayed_in_api: notice.displayed_in_api,
  displayed_in_overlay: notice.displayed_in_overlay,
  displayed_in_privacy_center: notice.displayed_in_privacy_center,
  notice_key: notice.notice_key,
  description: notice.description,
  disabled: notice.disabled,
  has_gpc_flag: notice.has_gpc_flag,
  id: notice.id,
  internal_description: notice.internal_description,
  origin: notice.origin,
});

export const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Title"),
  regions: Yup.array(Yup.string())
    .min(1, "Must assign at least one location")
    .label("Locations"),
});
