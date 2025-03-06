import { ConsentMethod, UserConsentPreference } from "~/types/api";

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
  string
> = {
  [UserConsentPreference.OPT_IN]: "success",
  [UserConsentPreference.OPT_OUT]: "error",
  [UserConsentPreference.ACKNOWLEDGE]: "caution",
  [UserConsentPreference.TCF]: "caution",
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
};
