import { CONSENT_USE_OPTIONS } from "~/features/configure-consent/constants";

export const dataUseIsConsentUse = (dataUse: string) =>
  CONSENT_USE_OPTIONS.some((opt) => opt.value === dataUse.split(".")[0]);
