import {
  ConsentMechanism,
  FidesAttStatus,
  PrivacyNoticeWithPreference,
} from "../consent-types";

/**
 * When ATT is denied, non-exempt custom notices must start as opted-out regardless of
 * what the FidesJS cookie says.
 *
 * Why this is needed:
 * The FidesJS cookie persists user consent across sessions. In the TCF overlay, the
 * draft state (draftIds.customPurposesConsent) is initialized from that cookie. If a
 * returning user previously opted-in to a custom notice, the cookie has it as opted-in,
 * so the draft includes it — and handleAcceptAll / handleRejectAll both preserve
 * disabled-but-opted-in draft IDs (to handle notice_only notices that are always opt-in).
 *
 * ATT-denied non-exempt notices are the opposite of notice_only: they're locked at
 * OPT-OUT by a system constraint, not opt-in by design. If we leave their cookie
 * value in the draft, Accept All and Reject All will incorrectly preserve them as
 * opted-in and save that back to the API.
 *
 * Fix: strip non-exempt ATT notices from the draft at initialization. With them absent
 * from draftIds, the existing handleAcceptAll / handleRejectAll logic automatically
 * excludes them from the opted-in set (their disabled=true keeps them out of Accept All,
 * and they're absent from draftIds so Reject All doesn't preserve them either).
 *
 * notice_only notices are kept — they're a separate concept (always opt-in regardless
 * of ATT) and must remain in the draft.
 */
export const filterAttDeniedFromDraft = (
  draftIds: string[],
  notices: Array<PrivacyNoticeWithPreference>,
  fidesAttStatus: FidesAttStatus | undefined,
): string[] => {
  if (
    fidesAttStatus !== FidesAttStatus.DENIED &&
    fidesAttStatus !== FidesAttStatus.RESTRICTED
  ) {
    return draftIds;
  }
  const noticeMap = new Map(notices.map((n) => [n.id, n]));
  return draftIds.filter((id) => {
    const notice = noticeMap.get(id);
    // Keep notice_only notices (always locked opt-in regardless of ATT).
    // Keep att_exempt notices (user can still interact with these when ATT is denied).
    // Remove everything else — non-exempt ATT notices must start as opted-out.
    return (
      notice?.consent_mechanism === ConsentMechanism.NOTICE_ONLY ||
      notice?.att_exempt === true
    );
  });
};
