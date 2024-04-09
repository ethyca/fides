import { Divider, Stack, useToast } from "@fidesui/react";
import React, { useEffect, useMemo, useState } from "react";
import {
  NoticeConsent,
  getConsentContext,
  getOrMakeFidesCookie,
  removeCookiesFromBrowser,
  saveFidesCookie,
  transformUserPreferenceToBoolean,
  getGpcStatusFromNotice,
  PrivacyNotice,
  ConsentContext,
  FidesCookie,
  PrivacyNoticeWithPreference,
  noticeHasConsentInCookie,
  transformConsentToFidesUserPreference,
} from "fides-js";
import { useAppSelector } from "~/app/hooks";
import {
  selectUserRegion,
  selectPrivacyExperience,
  useUpdatePrivacyPreferencesMutation,
  useUpdateNoticesServedMutation,
} from "~/features/consent/consent.slice";

import {
  ConsentMechanism,
  ConsentMethod,
  ConsentOptionCreate,
  PrivacyNoticeResponseWithUserPreferences,
  PrivacyPreferencesRequest,
  ServingComponent,
  UserConsentPreference,
} from "~/types/api";
import { useRouter } from "next/router";
import { inspectForBrowserIdentities } from "~/common/browser-identities";
import { NoticeHistoryIdToPreference } from "~/features/consent/types";
import { ErrorToastOptions, SuccessToastOptions } from "~/common/toast-options";
import { useI18n } from "~/common/i18nContext";
import { selectBestNoticeTranslation } from "fides-js";
import { useLocalStorage } from "~/common/hooks";
import ConsentItem from "./ConsentItem";
import SaveCancel from "./SaveCancel";
import PrivacyPolicyLink from "./PrivacyPolicyLink";

// DEFER(fides#3505): Use the fides-js version of this function
export const resolveConsentValue = (
  notice: PrivacyNoticeResponseWithUserPreferences,
  context: ConsentContext,
  cookie: FidesCookie
): UserConsentPreference | undefined => {
  if (notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY) {
    return UserConsentPreference.ACKNOWLEDGE;
  }
  const gpcEnabled =
    !!notice.has_gpc_flag &&
    context.globalPrivacyControl === true &&
    !noticeHasConsentInCookie(
      notice as PrivacyNoticeWithPreference,
      cookie.consent
    );
  if (gpcEnabled) {
    return UserConsentPreference.OPT_OUT;
  }
  const preferenceExistsInCookie = noticeHasConsentInCookie(
    notice as PrivacyNoticeWithPreference,
    cookie.consent
  );
  if (preferenceExistsInCookie) {
    return transformConsentToFidesUserPreference(
      // @ts-ignore
      cookie.consent[notice.notice_key],
      notice.consent_mechanism
    );
  }

  return notice.default_preference;
};

const NoticeDrivenConsent = ({ base64Cookie }: { base64Cookie: boolean }) => {
  const router = useRouter();
  const toast = useToast();
  const [consentRequestId] = useLocalStorage("consentRequestId", "");
  const [verificationCode] = useLocalStorage("verificationCode", "");
  const consentContext = useMemo(() => getConsentContext(), []);
  const experience = useAppSelector(selectPrivacyExperience);
  const cookie = useMemo(() => getOrMakeFidesCookie(), []);
  const { fides_user_device_id: fidesUserDeviceId } = cookie.identity;
  const [updatePrivacyPreferencesMutationTrigger] =
    useUpdatePrivacyPreferencesMutation();
  const region = useAppSelector(selectUserRegion);
  const { i18n } = useI18n();

  const browserIdentities = useMemo(() => {
    const identities = inspectForBrowserIdentities();
    const deviceIdentity = { fides_user_device_id: fidesUserDeviceId };
    return identities ? { ...deviceIdentity, ...identities } : deviceIdentity;
  }, [fidesUserDeviceId]);

  const initialDraftPreferences: NoticeHistoryIdToPreference = useMemo(() => {
    const newPreferences: NoticeHistoryIdToPreference = {};
    if (experience?.privacy_notices) {
      experience.privacy_notices.forEach((notice) => {
        const pref: UserConsentPreference | undefined = resolveConsentValue(
          notice,
          consentContext,
          cookie
        );
        if (pref) {
          // todo- set to default language, extract into helper util fn to keep this logic centralized.
          newPreferences[notice.translations[0].privacy_notice_history_id] =
            pref;
        } else {
          newPreferences[notice.translations[0].privacy_notice_history_id] =
            UserConsentPreference.OPT_OUT;
        }
      });
    }
    return newPreferences;
  }, [experience, consentContext, cookie]);

  const [draftPreferences, setDraftPreferences] =
    useState<NoticeHistoryIdToPreference>(initialDraftPreferences);

  useEffect(() => {
    setDraftPreferences(initialDraftPreferences);
  }, [initialDraftPreferences]);

  const [updateNoticesServedMutationTrigger, { data: servedNotice }] =
    useUpdateNoticesServedMutation();

  useEffect(() => {
    if (experience && experience.privacy_notices) {
      updateNoticesServedMutationTrigger({
        id: consentRequestId,
        body: {
          browser_identity: browserIdentities,
          // TODO (PROD-1748): pass in specific language shown in UI
          privacy_experience_config_history_id:
            experience?.experience_config?.translations[0]
              .privacy_experience_config_history_id,
          // TODO (PROD-1748): pass in specific language shown in UI
          privacy_notice_history_ids: experience.privacy_notices.map(
            // @ts-ignore
            (p: PrivacyNotice) => p.translations[0].privacy_notice_history_id
          ),
          serving_component: ServingComponent.PRIVACY_CENTER,
          user_geography: region,
        },
      });
    }
  }, [
    consentRequestId,
    updateNoticesServedMutationTrigger,
    experience,
    browserIdentities,
    region,
  ]);

  const items = useMemo(() => {
    if (!experience) {
      return [];
    }
    const { privacy_notices: notices } = experience;
    if (!notices || notices.length === 0) {
      return [];
    }

    return notices.map((notice) => {
      const preference =
        draftPreferences[notice.translations[0].privacy_notice_history_id];
      const value = transformUserPreferenceToBoolean(preference);
      const gpcStatus = getGpcStatusFromNotice({
        value,
        notice: notice as PrivacyNotice,
        consentContext,
      });

      const bestTranslation = selectBestNoticeTranslation(
        i18n,
        notice as PrivacyNotice
      );

      return {
        name: notice.name || "",
        description: notice.translations[0].description || "",
        id: notice.id,
        historyId: notice.translations[0].privacy_notice_history_id,
        highlight: false,
        url: undefined,
        value,
        gpcStatus,
        disabled: notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY,
        bestTranslation,
      };
    });
  }, [consentContext, experience, draftPreferences, i18n]);

  const handleCancel = () => {
    router.push("/");
  };

  /**
   * When saving, we need to:
   * 1. Send PATCH to Fides backend
   * 2. Save to cookie and window object
   * 3. Delete any cookies that have been opted out of
   */
  const handleSave = async () => {
    const notices = experience?.privacy_notices ?? [];

    // Reconnect preferences to notices
    const noticePreferences = Object.entries(draftPreferences).map(
      ([historyKey, preference]) => {
        const notice = notices.find(
          // TODO (PROD-1748): pass in specific language shown in UI
          (n) => n.translations[0].privacy_notice_history_id === historyKey
        );
        return { historyKey, preference, notice };
      }
    );

    const preferences: ConsentOptionCreate[] = noticePreferences.map(
      ({ historyKey, preference, notice }) => {
        if (notice?.consent_mechanism === ConsentMechanism.NOTICE_ONLY) {
          return {
            privacy_notice_history_id: historyKey,
            preference: UserConsentPreference.ACKNOWLEDGE,
          };
        }
        return {
          privacy_notice_history_id: historyKey,
          preference: preference ?? UserConsentPreference.OPT_OUT,
        };
      }
    );

    const payload: PrivacyPreferencesRequest = {
      browser_identity: browserIdentities,
      preferences,
      user_geography: region,
      // TODO (PROD-1748): pass in specific language shown in UI
      privacy_experience_config_history_id:
        experience?.experience_config?.translations[0]
          .privacy_experience_config_history_id,
      method: ConsentMethod.SAVE,
      code: verificationCode,
      served_notice_history_id: servedNotice?.served_notice_history_id,
    };

    // 1. Send PATCH to Fides backend
    const result = await updatePrivacyPreferencesMutationTrigger({
      id: consentRequestId,
      body: payload,
    });
    const isError = "error" in result;
    if (isError || !result.data.preferences) {
      let description = "No preferences returned";
      if (isError) {
        description = typeof result.error === "string" ? result.error : "";
      }
      toast({
        title: "An error occurred while saving user consent preferences",
        description,
        ...ErrorToastOptions,
      });
      return;
    }

    // 2. Save the cookie and window obj on success
    const noticeKeyMap = new Map<string, boolean>(
      noticePreferences.map((preference) => [
        preference.notice?.notice_key || "",
        transformUserPreferenceToBoolean(preference.preference),
      ])
    );
    const noticeConsent: NoticeConsent = Object.fromEntries(noticeKeyMap);
    window.Fides.consent = noticeConsent;
    const updatedCookie = { ...cookie, consent: noticeConsent };
    updatedCookie.fides_meta.consentMethod = ConsentMethod.SAVE; // include the consentMethod as extra metadata
    saveFidesCookie(updatedCookie, base64Cookie);
    toast({
      title: "Your consent preferences have been saved",
      ...SuccessToastOptions,
    });

    // 3. Delete any cookies that have been opted out of
    noticePreferences.forEach((noticePreference) => {
      if (
        noticePreference.preference === UserConsentPreference.OPT_OUT &&
        noticePreference.notice
      ) {
        removeCookiesFromBrowser(noticePreference.notice.cookies);
      }
    });
    router.push("/");
  };

  return (
    <Stack spacing={6} paddingX={12}>
      {items.map((item, index) => {
        const { id, highlight, url, name, description, historyId, disabled } =
          item;
        const handleChange = (value: boolean) => {
          const pref = value
            ? UserConsentPreference.OPT_IN
            : UserConsentPreference.OPT_OUT;
          setDraftPreferences({
            ...draftPreferences,
            ...{ [historyId]: pref },
          });
        };

        return (
          <React.Fragment key={id}>
            {index > 0 ? <Divider /> : null}
            <ConsentItem
              id={id}
              name={item.bestTranslation?.title}
              description={item.bestTranslation?.description}
              highlight={highlight}
              url={url}
              value={item.value}
              gpcStatus={item.gpcStatus}
              onChange={handleChange}
              disabled={disabled}
            />
          </React.Fragment>
        );
      })}
      <SaveCancel
        onSave={handleSave}
        onCancel={handleCancel}
        justifyContent="center"
      />
      <PrivacyPolicyLink alignSelf="center" experience={experience} />
    </Stack>
  );
};

export default NoticeDrivenConsent;
