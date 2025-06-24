import { getConsentContext } from "./consent-context";
import { readConsentFromAnyProvider } from "./consent-migration";
import {
  ConsentMechanism,
  ConsentMethod,
  FidesGlobal,
  NoticeConsent,
} from "./consent-types";
import { decodeNoticeConsentString } from "./consent-utils";
import { getFidesConsentCookie } from "./cookie";
import { decodeFidesString } from "./fides-string";
import { updateConsent } from "./preferences";
import {
  noticeHasConsentInCookie,
  transformUserPreferenceToBoolean,
} from "./shared-consent-utils";

/**
 * Opt out of notices that can be opted out of automatically.
 * This does not currently do anything with TCF unless the experience has custom notices applied.
 * Returns true if GPC or Notice Consent string has been applied
 */
export const automaticallyApplyPreferences = async (
  fidesGlobal: Pick<
    FidesGlobal,
    | "experience"
    | "saved_consent"
    | "cookie"
    | "geolocation"
    | "options"
    | "locale"
  >,
): Promise<boolean> => {
  const { experience, saved_consent: savedConsent, options } = fidesGlobal;
  // Early-exit if there is no experience or notices, since we've nothing to do
  if (
    !experience ||
    !experience.experience_config ||
    !experience.privacy_notices?.length
  ) {
    return false;
  }

  const context = getConsentContext();
  // let fidesString: string | undefined;
  const { nc: noticeConsentString } = decodeFidesString(
    options.fidesString || "",
  );
  if (context.globalPrivacyControl) {
    fidesDebugger("GPC is enabled");
  }
  if (noticeConsentString) {
    fidesDebugger("Notice consent string found", noticeConsentString);
    // fidesString = fidesOptions.fidesString!;
  }

  // Check for migrated consent from OneTrust
  const { consent: migratedConsent, method: migrationMethod } =
    readConsentFromAnyProvider(options);
  const hasMigratedConsent =
    !!migratedConsent && !!migrationMethod && !getFidesConsentCookie();

  if (
    !context.globalPrivacyControl &&
    !noticeConsentString &&
    !hasMigratedConsent
  ) {
    return false;
  }

  let gpcApplied = false;
  let noticeConsentApplied = false;
  let migratedConsentApplied = false;

  const noticeConsentToSave = experience.privacy_notices.reduce(
    (accumulator, notice) => {
      const appliedConsent = { ...accumulator };
      const defaultBoolean = transformUserPreferenceToBoolean(
        notice.default_preference,
      );
      appliedConsent[notice.notice_key] = defaultBoolean;
      if (savedConsent[notice.notice_key]) {
        appliedConsent[notice.notice_key] = savedConsent[notice.notice_key];
      }
      const hasPriorConsent = noticeHasConsentInCookie(notice, savedConsent);
      const isNoticeOnly =
        notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY;

      // First check for migrated consent
      if (hasMigratedConsent && migratedConsent) {
        const preference = migratedConsent[notice.notice_key];
        if (preference !== undefined) {
          migratedConsentApplied = true;
          appliedConsent[notice.notice_key] = preference;
          return appliedConsent;
        }
      }

      if (isNoticeOnly) {
        // We always match consent vals one-to-one from OT, even if it's
        // "false" on a notice_only notice. If there's no OT preference, we
        // keep the default preference for notice_only notices.
        return appliedConsent;
      }

      // Then check for notice consent string
      if (noticeConsentString) {
        const noticeConsent = decodeNoticeConsentString(noticeConsentString);
        const preference = noticeConsent[notice.notice_key];
        if (preference !== undefined) {
          noticeConsentApplied = true;
          appliedConsent[notice.notice_key] = preference;
          return appliedConsent;
        }
      }

      // Then check for GPC
      if (context.globalPrivacyControl && !hasPriorConsent) {
        if (notice.has_gpc_flag) {
          gpcApplied = true;
          appliedConsent[notice.notice_key] = false;
          return appliedConsent;
        }
      }

      return appliedConsent;
    },
    {} as NoticeConsent,
  );

  if (gpcApplied || noticeConsentApplied || migratedConsentApplied) {
    let consentMethod: ConsentMethod = ConsentMethod.SCRIPT;
    if (migratedConsentApplied && migrationMethod) {
      fidesDebugger("Updating consent preferences with migrated consent");
      consentMethod = migrationMethod;
    } else if (noticeConsentApplied) {
      fidesDebugger("Updating consent preferences with Notice Consent string");
      consentMethod = ConsentMethod.SCRIPT;
    } else if (gpcApplied) {
      fidesDebugger("Updating consent preferences with GPC");
      consentMethod = ConsentMethod.GPC;
    }

    await updateConsent(fidesGlobal, {
      noticeConsent: noticeConsentToSave,
      consentMethod,
    });
    return true;
  }
  return false;
};
