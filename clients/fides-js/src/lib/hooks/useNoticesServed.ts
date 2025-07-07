import { useCallback, useEffect } from "preact/hooks";

import { patchNoticesServed } from "../../services/api";
import {
  FidesInitOptions,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  RecordConsentServedRequest,
  ServingComponent,
} from "../consent-types";
import { FidesEvent } from "../events";
import { sessionManager } from "../session-manager";

interface UseNoticesServedProps {
  options: FidesInitOptions;
  privacyExperience: PrivacyExperience | PrivacyExperienceMinimal;
  privacyExperienceConfigHistoryId?: string;
  privacyNoticeHistoryIds?: string[];
  userGeography?: string;
  acknowledgeMode?: boolean;
  tcfNoticesServed?: Partial<RecordConsentServedRequest>;
}

export const useNoticesServed = ({
  options,
  privacyExperience,
  privacyExperienceConfigHistoryId,
  privacyNoticeHistoryIds,
  userGeography,
  acknowledgeMode,
  tcfNoticesServed,
}: UseNoticesServedProps) => {
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

      // Use the session-level served_notice_history_id for consistency
      const sessionServedNoticeHistoryId =
        sessionManager.getServedNoticeHistoryId();

      // Construct the notices-served API request and send!
      const request: RecordConsentServedRequest = {
        served_notice_history_id: sessionServedNoticeHistoryId,
        browser_identity: event.detail.identity,
        privacy_experience_config_history_id:
          privacyExperienceConfigHistoryId || "",
        user_geography: userGeography,
        acknowledge_mode: acknowledgeMode,
        privacy_notice_history_ids: privacyNoticeHistoryIds || [],
        serving_component: String(event.detail.extraDetails.servingComponent),
        property_id: privacyExperience.property_id,
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
      tcfNoticesServed,
    ],
  );

  useEffect(() => {
    window.addEventListener("FidesUIShown", handleUIEvent);
    return () => {
      window.removeEventListener("FidesUIShown", handleUIEvent);
    };
  }, [handleUIEvent]);
};
export default useNoticesServed;
