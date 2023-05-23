import { UserConsentPreference } from "~/types/api";

export type FidesKeyToConsent = {
  [fidesKey: string]: boolean | undefined;
};

export type NoticeHistoryIdToPreference = {
  [historyId: string]: UserConsentPreference | undefined;
};

export enum GpcStatus {
  /** GPC is not relevant for the consent option. */
  NONE = "none",
  /** GPC is enabled and consent matches the configured default. */
  APPLIED = "applied",
  /** GPC is enabled but consent has been set to override the configured default. */
  OVERRIDDEN = "overridden",
}
