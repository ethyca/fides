import { ConsentContext } from "./consent-context";
import {
  ConsentMechanism,
  ConsentMethod,
  FidesGlobal,
  NoticeConsent,
  PrivacyExperience,
  PrivacyExperienceMinimal,
} from "./consent-types";
import {
  constructFidesRegionString,
  decodeNoticeConsentString,
} from "./consent-utils";
import { fidesLifecycleManager } from "./fides-lifecycle-manager";
import { DEFAULT_LOCALE, selectBestExperienceConfigTranslation } from "./i18n";
import { savePreferencesApi } from "./preferences";
import {
  buildConsentPreferencesArray,
  noticeHasConsentInCookie,
  transformUserPreferenceToBoolean,
} from "./shared-consent-utils";

/**
 * Calculates automated consent preferences from GPC, migrated consent, and notice consent strings.
 * This is a pure function with no side effects - it only calculates what consent should be applied.
 *
 * @param experience - The privacy experience configuration
 * @param savedConsent - The user's saved consent preferences
 * @param context - The automated consent context containing GPC, migrated consent, and notice consent strings
 * @returns Object containing the calculated notice consent, consent method, and whether any automated consent was applied
 */
export const calculateAutomatedConsent = (
  experience: PrivacyExperience,
  savedConsent: NoticeConsent,
  context: ConsentContext,
): {
  noticeConsent: NoticeConsent;
  consentMethod: ConsentMethod | null;
  applied: boolean;
} => {
  // Early-exit if there is no experience or notices
  if (
    !experience ||
    !experience.experience_config ||
    !experience.privacy_notices?.length
  ) {
    return {
      noticeConsent: {},
      consentMethod: null,
      applied: false,
    };
  }

  const {
    globalPrivacyControl,
    migratedConsent,
    migrationMethod,
    noticeConsentString,
    hasFidesCookie,
  } = context;

  // Check if we have migrated consent (only applies if no Fides cookie exists yet)
  const hasMigratedConsent =
    !!migratedConsent && !!migrationMethod && !hasFidesCookie;

  // Early-exit if no automated consent sources are available
  if (!globalPrivacyControl && !noticeConsentString && !hasMigratedConsent) {
    return {
      noticeConsent: {},
      consentMethod: null,
      applied: false,
    };
  }

  if (globalPrivacyControl) {
    fidesDebugger("GPC is enabled");
  }
  if (noticeConsentString) {
    fidesDebugger("Notice consent string found", noticeConsentString);
  }

  let gpcApplied = false;
  let noticeConsentApplied = false;
  let migratedConsentApplied = false;

  const noticeConsentToSave: NoticeConsent = experience.privacy_notices.reduce(
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
      if (hasMigratedConsent) {
        const preference = migratedConsent[notice.notice_key];
        if (preference !== undefined) {
          migratedConsentApplied = true;
          appliedConsent[notice.notice_key] = preference;
          return appliedConsent;
        }
      }

      if (isNoticeOnly) {
        // We always match consent vals one-to-one from migrated providers, even if it's
        // "false" on a notice_only notice. If there's no migrated preference, we
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
      if (globalPrivacyControl && !hasPriorConsent) {
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
      fidesDebugger("Calculated automated consent from migrated provider");
      consentMethod = migrationMethod;
    } else if (noticeConsentApplied) {
      fidesDebugger("Calculated automated consent from Notice Consent string");
      consentMethod = ConsentMethod.SCRIPT;
    } else if (gpcApplied) {
      fidesDebugger("Calculated automated consent from GPC");
      consentMethod = ConsentMethod.GPC;
    }

    return {
      noticeConsent: noticeConsentToSave,
      consentMethod,
      applied: true,
    };
  }

  return {
    noticeConsent: {},
    consentMethod: null,
    applied: false,
  };
};

/**
 * Saves automated consent preferences to the Fides API.
 * This function ONLY persists consent to the backend - it does NOT update the cookie,
 * window.Fides object, or dispatch events (those are already done during initialization).
 *
 * @param fidesGlobal - The Fides global state
 * @param noticeConsent - The notice consent preferences to save
 * @param consentMethod - The consent method (e.g., GPC, SCRIPT)
 */
export const saveAutomatedPreferencesToApi = async (
  fidesGlobal: Pick<FidesGlobal, "experience" | "cookie" | "config" | "locale">,
  noticeConsent: NoticeConsent,
  consentMethod: ConsentMethod,
): Promise<void> => {
  const { experience, cookie, config, locale } = fidesGlobal;

  if (
    !experience ||
    !cookie ||
    !config ||
    config.options.fidesDisableSaveApi ||
    !experience.privacy_notices
  ) {
    return;
  }

  const { options } = config;

  try {
    // Build SaveConsentPreference array using shared utility
    const consentPreferencesToSave = buildConsentPreferencesArray(
      noticeConsent,
      experience.privacy_notices,
      locale || DEFAULT_LOCALE,
      DEFAULT_LOCALE,
      false, // Return minimal objects with just noticeHistoryId and consentPreference
    );

    if (consentPreferencesToSave.length === 0) {
      return;
    }

    // Get privacy_experience_config_history_id from experience config translations
    let configHistoryId: string | undefined;
    if (experience.experience_config?.translations?.length) {
      const bestExperienceConfigTranslation =
        selectBestExperienceConfigTranslation(
          locale || DEFAULT_LOCALE,
          DEFAULT_LOCALE,
          experience.experience_config,
        );
      configHistoryId =
        bestExperienceConfigTranslation?.privacy_experience_config_history_id;
    }

    // Get user geography string from config.geolocation
    const userLocationString = constructFidesRegionString(config.geolocation);

    // Get served notice history ID
    const servedNoticeHistoryId =
      fidesLifecycleManager.getServedNoticeHistoryId();

    // Call savePreferencesApi to handle the API request
    await savePreferencesApi(
      options,
      cookie,
      experience as PrivacyExperience | PrivacyExperienceMinimal,
      consentMethod,
      configHistoryId,
      consentPreferencesToSave,
      undefined, // tcf
      userLocationString,
      servedNoticeHistoryId,
    );
  } catch (error) {
    fidesDebugger("Error saving automated preferences to API:", error);
    // Don't throw - we don't want to block if the API call fails
  }
};
