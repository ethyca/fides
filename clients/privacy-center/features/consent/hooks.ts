import { getOrMakeFidesCookie } from "fides-js";
import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { PrivacyNoticeRegion } from "~/types/api";
import {
  selectIsNoticeDriven,
  useSettings,
} from "~/features/common/settings.slice";
import {
  useGetPrivacyExperienceQuery,
  setFidesUserDeviceId,
  useGetUserGeolocationQuery,
  selectUserRegion,
} from "./consent.slice";

/**
 * Subscribes to the relevant privacy experience.
 *
 * 1. Queries for the user's geolocation using geolocation settings
 * 2. Gets the device ID from the cookie
 * 3. Queries for the experience, which requires both location and device ID.
 * By calling this hook, the selector for experiences should then be populated.
 *
 * const experience = useAppSelector(selectPrivacyExperience);
 *
 * Skips the subscription if notices are not enabled via settings or if
 * there is no region available.
 */
export const useSubscribeToPrivacyExperienceQuery = () => {
  const dispatch = useAppDispatch();
  const { IS_GEOLOCATION_ENABLED, GEOLOCATION_API_URL } = useSettings();
  const cookie = getOrMakeFidesCookie();
  const { fides_user_device_id: fidesUserDeviceId } = cookie.identity;

  const skipFetchExperience = !useAppSelector(selectIsNoticeDriven);
  const skipFetchGeolocation =
    skipFetchExperience || !IS_GEOLOCATION_ENABLED || !GEOLOCATION_API_URL;

  useGetUserGeolocationQuery(GEOLOCATION_API_URL, {
    skip: skipFetchGeolocation,
  });

  useEffect(() => {
    dispatch(setFidesUserDeviceId(fidesUserDeviceId));
  }, [dispatch, fidesUserDeviceId]);

  const region = useAppSelector(selectUserRegion);
  const params = {
    // Casting should be safe because we skip in the hook below if region does not exist
    region: region as PrivacyNoticeRegion,
    fides_user_device_id: fidesUserDeviceId,
  };
  useGetPrivacyExperienceQuery(params, {
    skip: !region || skipFetchExperience,
  });
};
