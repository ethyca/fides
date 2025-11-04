import { CUSTOM_TAG_COLOR } from "fidesui";

import {
  ConsentMethod,
  RequestOrigin,
  UserConsentPreference,
} from "~/types/api";

export const USER_CONSENT_PREFERENCE_LABELS: Record<
  UserConsentPreference,
  string
> = {
  [UserConsentPreference.OPT_IN]: "Opt in",
  [UserConsentPreference.OPT_OUT]: "Opt out",
  [UserConsentPreference.ACKNOWLEDGE]: "Acknowledge",
  [UserConsentPreference.TCF]: "TCF",
};

export const USER_CONSENT_PREFERENCE_COLOR: Record<
  UserConsentPreference,
  CUSTOM_TAG_COLOR
> = {
  [UserConsentPreference.OPT_IN]: CUSTOM_TAG_COLOR.SUCCESS,
  [UserConsentPreference.OPT_OUT]: CUSTOM_TAG_COLOR.ERROR,
  [UserConsentPreference.ACKNOWLEDGE]: CUSTOM_TAG_COLOR.DEFAULT,
  [UserConsentPreference.TCF]: CUSTOM_TAG_COLOR.SANDSTONE,
};

export const CONSENT_METHOD_LABELS: Record<ConsentMethod, string> = {
  [ConsentMethod.ACCEPT]: "Accept",
  [ConsentMethod.BUTTON]: "Button",
  [ConsentMethod.DISMISS]: "Dismiss",
  [ConsentMethod.GPC]: "GPC",
  [ConsentMethod.REJECT]: "Reject",
  [ConsentMethod.SAVE]: "Save",
  [ConsentMethod.SCRIPT]: "Script",
  [ConsentMethod.INDIVIDUAL_NOTICE]: "Individual Notice",
  [ConsentMethod.ACKNOWLEDGE]: "Acknowledge",
  [ConsentMethod.EXTERNAL_PROVIDER]: "External Provider",
};

export const REQUEST_ORIGIN_LABELS: Record<RequestOrigin, string> = {
  [RequestOrigin.API]: "API",
  [RequestOrigin.BANNER_AND_MODAL]: "Banner and Modal",
  [RequestOrigin.MODAL]: "Modal",
  [RequestOrigin.OVERLAY]: "Overlay",
  [RequestOrigin.PRIVACY_CENTER]: "Privacy Center",
  [RequestOrigin.TCF_OVERLAY]: "TCF Overlay",
};
