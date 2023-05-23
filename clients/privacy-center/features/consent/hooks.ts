import { getOrMakeFidesCookie } from "fides-js";
import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { PrivacyNoticeRegion } from "~/types/api";
import { selectIsNoticeDriven } from "~/features/common/settings.slice";
import {
  useGetPrivacyExperienceQuery,
  setRegion,
  setFidesDeviceUserId,
  selectExperienceRegion,
} from "./consent.slice";

/**
 * Subscribes to the relevant privacy experience, passing in parameters
 * for the user's region and their fides_user_device_id. By calling this,
 * the selector for experiences should then be populated.
 *
 * const experience = useAppSelector(selectPrivacyExperience);
 *
 * Skips the subscription if notices are not enabled via settings.
 */
export const useSubscribeToPrivacyExperienceQuery = () => {
  const skip = !useAppSelector(selectIsNoticeDriven);
  const dispatch = useAppDispatch();
  const cookie = getOrMakeFidesCookie();
  const { fides_user_device_id: fidesUserDeviceId } = cookie.identity;

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
    skip: !region || skip,
  });
};
