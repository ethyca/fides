import { Divider, Stack } from "@fidesui/react";
import React, { useEffect, useMemo, useState } from "react";
import {
  ConsentContext,
  getConsentContext,
  getOrMakeFidesCookie,
  saveFidesCookie,
} from "fides-js";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  selectCurrentConsentPreferences,
  selectExperienceRegion,
  selectPrivacyExperience,
  setFidesDeviceUserId,
  setRegion,
  useGetPrivacyExperienceQuery,
  useUpdatePrivacyPreferencesUnverifiedMutation,
} from "~/features/consent/consent.slice";
import {
  getGpcStatusFromNotice,
  transformUserPreferenceToBoolean,
} from "~/features/consent/helpers";

import {
  ConsentMethod,
  ConsentOptionCreate,
  PrivacyNoticeRegion,
  PrivacyNoticeResponseWithUserPreferences,
  PrivacyPreferencesRequest,
  UserConsentPreference,
} from "~/types/api";
import { useRouter } from "next/router";
import { inspectForBrowserIdentities } from "~/common/browser-identities";
import { NoticeHistoryIdToPreference } from "~/features/consent/types";
import ConsentItem from "./ConsentItem";
import SaveCancel from "./SaveCancel";

const resolveConsentValue = (
  notice: PrivacyNoticeResponseWithUserPreferences,
  context: ConsentContext
) => {
  const gpcEnabled =
    !!notice.has_gpc_flag && context.globalPrivacyControl === true;
  if (gpcEnabled) {
    return UserConsentPreference.OPT_OUT;
  }
  return notice.default_preference;
};

const NoticeDrivenConsent = () => {
  const dispatch = useAppDispatch();
  const consentContext = useMemo(() => getConsentContext(), []);
  const experience = useAppSelector(selectPrivacyExperience);
  const serverPreferences = useAppSelector(selectCurrentConsentPreferences);
  const router = useRouter();
  const cookie = getOrMakeFidesCookie();
  const { fides_user_device_id: fidesUserDeviceId } = cookie.identity;
  const [updatePrivacyPreferencesUnverifiedMutationTrigger] =
    useUpdatePrivacyPreferencesUnverifiedMutation();

  useEffect(() => {
    // TODO: query for location
    dispatch(setRegion(PrivacyNoticeRegion.US_CA));
    dispatch(setFidesDeviceUserId(fidesUserDeviceId));
  }, [dispatch, fidesUserDeviceId]);

  const region = useAppSelector(selectExperienceRegion);
  const params = {
    // Casting should be safe because we skip in the hook below if region does not exist
    region: region as PrivacyNoticeRegion,
    fides_device_user_id: fidesUserDeviceId,
  };
  useGetPrivacyExperienceQuery(params, {
    skip: !region,
  });

  const initialDraftPreferences = useMemo(() => {
    const newPreferences = { ...serverPreferences };
    Object.entries(serverPreferences).forEach(([key, value]) => {
      if (!value) {
        const notices = experience?.privacy_notices ?? [];
        const notice = notices.filter(
          (n) => n.privacy_notice_history_id === key
        )[0];
        const defaultValue = notice
          ? resolveConsentValue(notice, consentContext)
          : UserConsentPreference.OPT_OUT;
        newPreferences[key] = defaultValue;
      }
    });
    return newPreferences;
  }, [serverPreferences, experience, consentContext]);

  const [draftPreferences, setDraftPreferences] =
    useState<NoticeHistoryIdToPreference>(initialDraftPreferences);

  useEffect(() => {
    setDraftPreferences(initialDraftPreferences);
  }, [initialDraftPreferences]);

  const items = useMemo(() => {
    if (!experience) {
      return [];
    }
    const { privacy_notices: notices } = experience;
    if (!notices || notices.length === 0) {
      return [];
    }

    return notices.map((notice) => {
      const preference = draftPreferences[notice.privacy_notice_history_id];
      const value = transformUserPreferenceToBoolean(preference);
      const gpcStatus = getGpcStatusFromNotice({
        value,
        notice,
        consentContext,
      });

      return {
        name: notice.name || "",
        description: notice.description || "",
        id: notice.id,
        historyId: notice.privacy_notice_history_id,
        highlight: false,
        url: undefined,
        value,
        gpcStatus,
      };
    });
  }, [consentContext, experience, draftPreferences]);

  const handleCancel = () => {
    router.push("/");
  };

  const handleSave = async () => {
    const browserIdentities = inspectForBrowserIdentities();
    const deviceIdentity = { fides_user_device_id: fidesUserDeviceId };
    const identities = browserIdentities
      ? { ...deviceIdentity, ...browserIdentities }
      : deviceIdentity;

    const preferences: ConsentOptionCreate[] = Object.entries(
      draftPreferences
    ).map(([key, value]) => ({
      privacy_notice_history_id: key,
      preference: value ?? UserConsentPreference.OPT_OUT,
    }));

    const payload: PrivacyPreferencesRequest = {
      browser_identity: identities,
      preferences,
      user_geography: region,
      privacy_experience_history_id: experience?.privacy_experience_history_id,
      method: ConsentMethod.BUTTON,
    };

    const result = await updatePrivacyPreferencesUnverifiedMutationTrigger(
      payload
    );
    if ("error" in result) {
      // TODO: handle error
    } else {
      // TODO: handle success
      // Save the cookie on success
      saveFidesCookie(cookie);
    }
  };

  return (
    <Stack spacing={4}>
      {items.map((item, index) => {
        const { id, highlight, url, name, description, historyId } = item;
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
              name={name}
              description={description}
              highlight={highlight}
              url={url}
              value={item.value}
              gpcStatus={item.gpcStatus}
              onChange={handleChange}
            />
          </React.Fragment>
        );
      })}
      <SaveCancel onSave={handleSave} onCancel={handleCancel} />
    </Stack>
  );
};

export default NoticeDrivenConsent;
