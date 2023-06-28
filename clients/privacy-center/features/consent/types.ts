import { UserConsentPreference } from "~/types/api";

export type FidesKeyToConsent = {
  [fidesKey: string]: boolean | undefined;
};

export type NoticeHistoryIdToPreference = {
  [historyId: string]: UserConsentPreference | undefined;
};
