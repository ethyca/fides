import { useEffect, useState, useCallback } from "preact/hooks";
import { FidesEvent } from "./events";
import {
  FidesInitOptions,
  PrivacyExperience,
  RecordConsentServedRequest,
  ServingComponent,
  RecordsServedResponse,
} from "./consent-types";
import { patchNoticesServed } from "../services/api";

/**
 * Hook which tracks if the app has mounted yet.
 *
 * Used to make sure the server and client UIs match for hydration
 * Adapted from https://www.joshwcomeau.com/react/the-perils-of-rehydration/
 */
export const useHasMounted = () => {
  const [hasMounted, setHasMounted] = useState(false);

  useEffect(() => {
    setHasMounted(true);
  }, []);

  return hasMounted;
};

/**
 * Hook to facilitate showing/hiding while adhering to WAI
 * based on chakra-ui's `useDisclosure`
 */
export const useDisclosure = ({ id }: { id: string }) => {
  const [isOpen, setIsOpen] = useState(false);

  const onClose = useCallback(() => setIsOpen(false), []);
  const onOpen = useCallback(() => setIsOpen(true), []);

  const onToggle = useCallback(() => {
    if (isOpen) {
      onClose();
    } else {
      onOpen();
    }
  }, [isOpen, onOpen, onClose]);

  const getButtonProps = () => ({
    "aria-expanded": isOpen,
    "aria-controls": id,
    onClick: onToggle,
  });

  const getDisclosureProps = () => ({
    id,
    className: isOpen ? "fides-disclosure-visible" : "fides-disclosure-hidden",
  });

  return {
    isOpen,
    onOpen,
    onClose,
    onToggle,
    getButtonProps,
    getDisclosureProps,
  };
};

/**
 * Extracts the id value of each object in the list and returns a list
 * of IDs, either strings or numbers based on the IDs' type.
 */
const extractIds = <T extends { id: string | number }[]>(
  modelList?: T
): any[] => {
  if (!modelList) {
    return [];
  }
  return modelList.map((model) => model.id);
};

export const useConsentServed = ({
  options,
  privacyExperience,
  privacyExperienceConfigHistoryId,
  privacyNoticeHistoryIds,
  userGeography,
  acknowledgeMode,
  propertyId,
}: {
  options: FidesInitOptions;
  privacyExperience: PrivacyExperience;
  privacyExperienceConfigHistoryId?: string;
  privacyNoticeHistoryIds?: string[];
  userGeography?: string;
  acknowledgeMode?: boolean;
  propertyId?: string;
}) => {
  const [servedNotice, setServedNotice] =
    useState<RecordsServedResponse | null>(null);

  const handleUIEvent = useCallback(
    async (event: FidesEvent) => {
      // Disable the notices-served API if the fides_disable_save_api option is set
      if (options.fidesDisableSaveApi) {
        return;
      }

      // Disable the notices-served API if the serving component is a regular
      // banner (or unknown!). This means we trigger the API for:
      // 1) MODAL
      // 2) TCF_OVERLAY
      // 3) TCF_BANNER
      if (
        !event.detail.extraDetails ||
        event.detail.extraDetails.servingComponent === ServingComponent.BANNER
      ) {
        return;
      }

      // Construct the notices-served API request and send!
      const request: RecordConsentServedRequest = {
        browser_identity: event.detail.identity,
        privacy_experience_config_history_id:
          privacyExperienceConfigHistoryId || "",
        user_geography: userGeography,
        acknowledge_mode: acknowledgeMode,
        privacy_notice_history_ids: privacyNoticeHistoryIds || [],
        tcf_purpose_consents: extractIds(
          privacyExperience?.tcf_purpose_consents
        ),
        tcf_purpose_legitimate_interests: extractIds(
          privacyExperience.tcf_purpose_legitimate_interests
        ),
        tcf_special_purposes: extractIds(
          privacyExperience?.tcf_special_purposes
        ),
        tcf_vendor_consents: extractIds(privacyExperience?.tcf_vendor_consents),
        tcf_vendor_legitimate_interests: extractIds(
          privacyExperience.tcf_vendor_legitimate_interests
        ),
        tcf_features: extractIds(privacyExperience?.tcf_features),
        tcf_special_features: extractIds(
          privacyExperience?.tcf_special_features
        ),
        tcf_system_consents: extractIds(privacyExperience?.tcf_system_consents),
        tcf_system_legitimate_interests: extractIds(
          privacyExperience?.tcf_system_legitimate_interests
        ),
        serving_component: String(event.detail.extraDetails.servingComponent),
        property_id: propertyId,
      };

      const result = await patchNoticesServed({
        request,
        options,
      });
      if (result) {
        setServedNotice(result);
      }
    },
    [
      privacyExperienceConfigHistoryId,
      privacyNoticeHistoryIds,
      options,
      acknowledgeMode,
      privacyExperience,
      userGeography,
      propertyId,
    ]
  );

  useEffect(() => {
    window.addEventListener("FidesUIShown", handleUIEvent);
    return () => {
      window.removeEventListener("FidesUIShown", handleUIEvent);
    };
  }, [handleUIEvent]);

  return { servedNotice };
};
