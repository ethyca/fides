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
  ConsentMechanism,
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

/**
 * Similar to fides-js resolveConsentValue, but uses notice logic instead of ConfigOption
 * TODO: Should this go in fides-js?
 */
const resolveConsentValue = (
  notice: PrivacyNoticeResponseWithUserPreferences,
  context: ConsentContext
) => {
  const gpcEnabled =
    !!notice.has_gpc_flag && context.globalPrivacyControl === true;

  if (notice.consent_mechanism === ConsentMechanism.OPT_IN) {
    return false;
  }

  if (notice.consent_mechanism === ConsentMechanism.OPT_OUT) {
    // If this notice has_gpc_flag and gpc is enabled in the browser, we should
    // automatically default to opt out (false)
    if (gpcEnabled) {
      return false;
    }
    return true;
  }

  // Notice only
  return true;
};

const NoticeDrivenConsent = () => {
  const dispatch = useAppDispatch();
  const consentContext = useMemo(() => getConsentContext(), []);
  const experience = useAppSelector(selectPrivacyExperience);
  const userPreferences = useAppSelector(selectCurrentConsentPreferences);
  const router = useRouter();
  const cookie = getOrMakeFidesCookie();
  const { fides_user_device_id: fidesUserDeviceId } = cookie.identity;
  const [updatePrivacyPreferencesUnverifiedMutationTrigger] =
    useUpdatePrivacyPreferencesUnverifiedMutation();

  const [newPreferences, setNewPreferences] =
    useState<NoticeHistoryIdToPreference>(userPreferences);

  useEffect(() => {
    // TODO: query for location
    dispatch(setRegion(PrivacyNoticeRegion.US_CA));
    dispatch(setFidesDeviceUserId(fidesUserDeviceId));
  }, [dispatch, fidesUserDeviceId]);

  // Make sure newPreferences is initialized properly
  useEffect(() => {
    setNewPreferences(userPreferences);
  }, [userPreferences]);

  const region = useAppSelector(selectExperienceRegion);
  const params = {
    // Casting should be safe because we skip in the hook below if region does not exist
    region: region as PrivacyNoticeRegion,
    fides_device_user_id: fidesUserDeviceId,
  };
  useGetPrivacyExperienceQuery(params, {
    skip: !region,
  });

  const items = useMemo(() => {
    if (!experience) {
      return [];
    }
    const { privacy_notices: notices } = experience;
    if (!notices || notices.length === 0) {
      return [];
    }

    return notices.map((notice) => {
      const defaultValue = resolveConsentValue(notice, consentContext);
      const preference = userPreferences[notice.privacy_notice_history_id];
      const value = preference
        ? transformUserPreferenceToBoolean(preference)
        : defaultValue;
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
  }, [consentContext, experience, userPreferences]);

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
      newPreferences
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

    console.log({ payload });

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
          setNewPreferences({ ...newPreferences, ...{ [historyId]: pref } });
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
