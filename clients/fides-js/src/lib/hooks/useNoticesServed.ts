import { useCallback, useEffect, useState } from "preact/hooks";
import { v4 as uuidv4 } from "uuid";

import { patchNoticesServed } from "../../services/api";
import {
  FidesInitOptions,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  RecordConsentServedRequest,
  ServingComponent,
} from "../consent-types";
import { FidesEvent } from "../events";

interface UseNoticesServedProps {
  options: FidesInitOptions;
  privacyExperience: PrivacyExperience | PrivacyExperienceMinimal;
  privacyExperienceConfigHistoryId?: string;
  privacyNoticeHistoryIds?: string[];
  userGeography?: string;
  acknowledgeMode?: boolean;
  propertyId?: string;
  tcfNoticesServed?: Partial<RecordConsentServedRequest>;
}

export const useNoticesServed = ({
  options,
  privacyExperience,
  privacyExperienceConfigHistoryId,
  privacyNoticeHistoryIds,
  userGeography,
  acknowledgeMode,
  propertyId,
  tcfNoticesServed,
}: UseNoticesServedProps) => {
  const [servedNoticeHistoryId, setServedNoticeHistoryId] =
    useState<string>(uuidv4());

  const handleUIEvent = useCallback(
    async (event: FidesEvent) => {
      // Disable the notices-served API if the fides_disable_save_api option or fides_disable_notices_served_api option is set
      if (options.fidesDisableSaveApi || options.fidesDisableNoticesServedApi) {
        return;
      }

      // Disable the notices-served API if the serving component is a regular
      // banner (or unknown!) unless the option for displaying notices in the
      // banner has been set. This means we trigger the API for:
      // 1) MODAL (both TCF and non-TCF)
      // 2) TCF_BANNER
      // 3) BANNER when show_layer1_notices is true
      if (
        !event.detail.extraDetails ||
        (event.detail.extraDetails.servingComponent ===
          ServingComponent.BANNER &&
          !(privacyExperience as PrivacyExperience)?.experience_config
            ?.show_layer1_notices)
      ) {
        return;
      }

      // Create new uuid for each served notice
      const newUUID = uuidv4();
      setServedNoticeHistoryId(newUUID);

      // Construct the notices-served API request and send!
      const request: RecordConsentServedRequest = {
        served_notice_history_id: newUUID,
        browser_identity: event.detail.identity,
        privacy_experience_config_history_id:
          privacyExperienceConfigHistoryId || "",
        user_geography: userGeography,
        acknowledge_mode: acknowledgeMode,
        privacy_notice_history_ids: privacyNoticeHistoryIds || [],
        serving_component: String(event.detail.extraDetails.servingComponent),
        property_id: propertyId,
        ...tcfNoticesServed,
      };

      // Send the request to the notices-served API
      patchNoticesServed({
        request,
        options,
      });
    },
    [
      options,
      privacyExperience,
      privacyExperienceConfigHistoryId,
      userGeography,
      acknowledgeMode,
      privacyNoticeHistoryIds,
      propertyId,
      tcfNoticesServed,
    ],
  );

  useEffect(() => {
    window.addEventListener("FidesUIShown", handleUIEvent);
    return () => {
      window.removeEventListener("FidesUIShown", handleUIEvent);
    };
  }, [handleUIEvent]);

  return { servedNoticeHistoryId };
};
export default useNoticesServed;
