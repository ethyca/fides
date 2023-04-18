import * as Yup from "yup";

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
  // Match backend defaults
  displayed_in_api: true,
  displayed_in_overlay: true,
  displayed_in_privacy_center: true,
};

export const transformPrivacyNoticeResponseToCreation = (
  notice: PrivacyNoticeResponse
): PrivacyNoticeCreation => {
  // Remove the fields not needed for editing/creation
  const {
    created_at: createdAt,
    updated_at: updatedAt,
    privacy_notice_history_id: historyId,
    version,
    ...rest
  } = notice;
  return {
    ...rest,
    name: notice.name ?? defaultInitialValues.name,
    regions: notice.regions ?? defaultInitialValues.regions,
    consent_mechanism:
      notice.consent_mechanism ?? defaultInitialValues.consent_mechanism,
    data_uses: notice.data_uses ?? defaultInitialValues.data_uses,
    enforcement_level:
      notice.enforcement_level ?? defaultInitialValues.enforcement_level,
  };
};

export const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Title"),
  data_uses: Yup.array(Yup.string())
    .min(1, "Must assign at least one data use")
    .label("Data uses"),
  regions: Yup.array(Yup.string())
    .min(1, "Must assign at least one location")
    .label("Locations"),
});
