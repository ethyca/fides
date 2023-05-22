import { Divider, Stack } from "@fidesui/react";
import React, { useEffect, useMemo } from "react";
import { ConsentContext, getConsentContext } from "fides-js";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  changeConsent,
  selectCurrentConsentPreferences,
  selectExperienceRegion,
  selectPrivacyExperience,
  setRegion,
  useGetPrivacyExperienceQuery,
} from "~/features/consent/consent.slice";
import { getGpcStatusFromNotice } from "~/features/consent/helpers";

import {
  ConsentMechanism,
  PrivacyNoticeRegion,
  PrivacyNoticeResponseWithUserPreferences,
} from "~/types/api";
import { useRouter } from "next/router";
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

  useEffect(() => {
    // TODO: query for location
    dispatch(setRegion(PrivacyNoticeRegion.US_CA));
  }, [dispatch]);

  const region = useAppSelector(selectExperienceRegion);
  useGetPrivacyExperienceQuery(region as PrivacyNoticeRegion, {
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
      // TODO(fides#3281): use notice key instead of notice.id
      const value = userPreferences[notice.id] ?? defaultValue;
      const gpcStatus = getGpcStatusFromNotice({
        value,
        notice,
        consentContext,
      });

      return {
        name: notice.name || "",
        description: notice.description || "",
        id: notice.id,
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
  const handleSave = () => {};

  return (
    <Stack spacing={4}>
      {items.map((item, index) => {
        const { id, highlight, url, name, description } = item;
        const handleChange = (value: boolean) => {
          dispatch(changeConsent({ key: id, value }));
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
