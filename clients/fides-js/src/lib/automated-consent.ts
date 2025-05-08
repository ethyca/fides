import { v4 as uuidv4 } from "uuid";

import { getConsentContext } from "./consent-context";
import { readConsentFromAnyProvider } from "./consent-migration";
import {
  ConsentMechanism,
  ConsentMethod,
  FidesCookie,
  FidesInitOptions,
  NoticeConsent,
  PrivacyExperience,
  SaveConsentPreference,
} from "./consent-types";
import { decodeNoticeConsentString } from "./consent-utils";
import { resolveConsentValue } from "./consent-value";
import {
  getFidesConsentCookie,
  updateCookieFromNoticePreferences,
} from "./cookie";
import { decodeFidesString } from "./fides-string";
import {
  I18n,
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
} from "./i18n";
import { updateConsentPreferences } from "./preferences";
import {
  noticeHasConsentInCookie,
  transformConsentToFidesUserPreference,
} from "./shared-consent-utils";

/**
 * Opt out of notices that can be opted out of automatically.
 * This does not currently do anything with TCF unless the experience has custom notices applied.
 * Returns true if GPC or Notice Consent string has been applied
 */
export const automaticallyApplyPreferences = async ({
  savedConsent,
  effectiveExperience,
  cookie,
  fidesRegionString,
  fidesOptions,
  i18n,
}: {
  savedConsent: NoticeConsent;
  effectiveExperience: PrivacyExperience;
  cookie: FidesCookie;
  fidesRegionString: string | null;
  fidesOptions: FidesInitOptions;
  i18n: I18n;
}): Promise<boolean> => {
  // Early-exit if there is no experience or notices, since we've nothing to do
  if (
    !effectiveExperience ||
    !effectiveExperience.experience_config ||
    !effectiveExperience.privacy_notices ||
    effectiveExperience.privacy_notices.length === 0
  ) {
    return false;
  }

  const context = getConsentContext();
  const { nc: noticeConsentString } = decodeFidesString(
    fidesOptions.fidesString || "",
  );
  if (context.globalPrivacyControl) {
    fidesDebugger("GPC is enabled");
  }
  if (noticeConsentString) {
    fidesDebugger("Notice consent string found", noticeConsentString);
  }

  // Check for migrated consent from OneTrust
  const { consent: migratedConsent, method: migrationMethod } =
    readConsentFromAnyProvider(fidesOptions);
  const hasMigratedConsent =
    !!migratedConsent && !!migrationMethod && !getFidesConsentCookie();

  if (
    !context.globalPrivacyControl &&
    !noticeConsentString &&
    !hasMigratedConsent
  ) {
    return false;
  }

  /**
   * Select the "best" translation that should be used for these saved
   * preferences based on the currently active locale.
   *
   * NOTE: This *feels* a bit weird, and would feel cleaner if this was moved
   * into the UI components. However, we currently want to keep the GPC
   * application isolated, so we need to duplicate some of that "best
   * translation" logic here.
   */
  const bestTranslation = selectBestExperienceConfigTranslation(
    i18n,
    effectiveExperience.experience_config,
  );
  const privacyExperienceConfigHistoryId =
    bestTranslation?.privacy_experience_config_history_id;

  let gpcApplied = false;
  let noticeConsentApplied = false;
  let migratedConsentApplied = false;

  const consentPreferencesToSave = effectiveExperience.privacy_notices.map(
    (notice) => {
      const hasPriorConsent = noticeHasConsentInCookie(notice, savedConsent);
      const bestNoticeTranslation = selectBestNoticeTranslation(i18n, notice);

      // First check for migrated consent
      if (hasMigratedConsent && migratedConsent) {
        const preference = migratedConsent[notice.notice_key];
        if (preference !== undefined) {
          migratedConsentApplied = true;
          const userPreference =
            typeof preference === "boolean"
              ? transformConsentToFidesUserPreference(
                  preference,
                  notice.consent_mechanism,
                )
              : preference;
          return new SaveConsentPreference(
            notice,
            userPreference,
            bestNoticeTranslation?.privacy_notice_history_id,
          );
        }
      }

      // Then check for notice consent string
      const noticeConsent = decodeNoticeConsentString(noticeConsentString);

      if (notice.consent_mechanism !== ConsentMechanism.NOTICE_ONLY) {
        // Notice Consent string takes precedence over GPC and overrides any prior consent
        if (noticeConsent) {
          const preference = noticeConsent[notice.notice_key];
          if (preference !== undefined) {
            noticeConsentApplied = true;
            return new SaveConsentPreference(
              notice,
              transformConsentToFidesUserPreference(
                preference,
                notice.consent_mechanism,
              ),
              bestNoticeTranslation?.privacy_notice_history_id,
            );
          }
        }
        // only apply GPC for notices that do not have prior consent
        if (
          context.globalPrivacyControl &&
          notice.has_gpc_flag &&
          !hasPriorConsent
        ) {
          fidesDebugger("Applying GPC to notice");
          gpcApplied = true;
          return new SaveConsentPreference(
            notice,
            transformConsentToFidesUserPreference(
              false,
              notice.consent_mechanism,
            ),
            bestNoticeTranslation?.privacy_notice_history_id,
          );
        }
      }
      return new SaveConsentPreference(
        notice,
        transformConsentToFidesUserPreference(
          resolveConsentValue(notice, savedConsent),
          notice.consent_mechanism,
        ),
        bestNoticeTranslation?.privacy_notice_history_id,
      );
    },
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
    await updateConsentPreferences({
      servedNoticeHistoryId: uuidv4(),
      consentPreferencesToSave,
      privacyExperienceConfigHistoryId,
      experience: effectiveExperience,
      consentMethod,
      options: fidesOptions,
      userLocationString: fidesRegionString || undefined,
      cookie,
      updateCookie: (oldCookie) =>
        updateCookieFromNoticePreferences(oldCookie, consentPreferencesToSave),
    });
    return true;
  }
  return false;
};
