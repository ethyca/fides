import { ConsentMechanism, EnforcementLevel } from "~/types/api";

export const MECHANISM_MAP = new Map([
  [ConsentMechanism.OPT_IN, "Opt in"],
  [ConsentMechanism.NOTICE_ONLY, "Notice only"],
  [ConsentMechanism.OPT_OUT, "Opt out"],
]);

export const ENFORCEMENT_LEVEL_MAP = new Map([
  [EnforcementLevel.SYSTEM_WIDE, "System wide"],
  [EnforcementLevel.FRONTEND, "Front end"],
  [EnforcementLevel.NOT_APPLICABLE, "Not applicable"],
]);

export const FRAMEWORK_MAP = new Map([
  ["gpp_us_national", "GPP US National"],
  ["gpp_us_state", "GPP US State"],
]);
