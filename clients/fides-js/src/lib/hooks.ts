import { useEffect, useState, useCallback } from "preact/hooks";
import { FidesEvent } from "./events";
import {
  FidesOptions,
  PrivacyExperience,
  LastServedConsentSchema,
  RecordConsentServedRequest,
  PrivacyNotice,
  ServingComponent,
} from "./consent-types";
import { patchNoticesServed } from "../services/fides/api";

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
  notices,
  options,
  userGeography,
  privacyExperience,
  acknowledgeMode,
}: {
  notices: PrivacyNotice[];
  options: FidesOptions;
  userGeography?: string;
  privacyExperience: PrivacyExperience;
  acknowledgeMode?: boolean;
}) => {
  const [servedNotices, setServedNotices] = useState<LastServedConsentSchema[]>(
    []
  );

  const handleUIEvent = useCallback(
    async (event: FidesEvent) => {
      // Only send notices-served request when we show via the modal since that
      // is the only time we show all notices.
      // When TCF is enabled, report notices served as soon as the banner is shown
      if (
        !event.detail.extraDetails ||
        (event.detail.extraDetails.servingComponent !==
          ServingComponent.OVERLAY &&
          event.detail.extraDetails.servingComponent !==
            ServingComponent.TCF_BANNER)
      ) {
        return;
      }
      const request: RecordConsentServedRequest = {
        browser_identity: event.detail.identity,
        privacy_experience_id: privacyExperience.id,
        user_geography: userGeography,
        acknowledge_mode: acknowledgeMode,
        privacy_notice_history_ids: notices.map(
          (n) => n.privacy_notice_history_id
        ),
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
        serving_component: event.detail.extraDetails.servingComponent,
      };
      const result = await patchNoticesServed({
        request,
        fidesApiUrl: options.fidesApiUrl,
        debug: options.debug,
      });
      if (result) {
        setServedNotices(result);
      }
    },
    [notices, options, acknowledgeMode, privacyExperience, userGeography]
  );

  useEffect(() => {
    window.addEventListener("FidesUIShown", handleUIEvent);
    return () => {
      window.removeEventListener("FidesUIShown", handleUIEvent);
    };
  }, [handleUIEvent]);

  return { servedNotices };
};
