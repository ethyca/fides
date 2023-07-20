import { useEffect, useState, useCallback } from "preact/hooks";
import { FidesEvent } from "./events";
import {
  FidesOptions,
  LastServedNoticeSchema,
  NoticesServedRequest,
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

export const useConsentServed = ({
  notices,
  options,
}: {
  notices: PrivacyNotice[];
  options: FidesOptions;
}) => {
  const [consentServed, setConsentServed] = useState(false);
  const [servedNotices, setServedNotices] = useState<
    LastServedNoticeSchema[] | undefined
  >(undefined);

  const handleUIEvent = useCallback(
    async (event: FidesEvent) => {
      if (consentServed) {
        return;
      }
      setConsentServed(true);
      const request: NoticesServedRequest = {
        browser_identity: window.Fides.identity, // TODO
        privacy_notice_history_ids: notices.map(
          (n) => n.privacy_notice_history_id
        ),
        serving_component: ServingComponent.BANNER, // TODO
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
    [consentServed, notices, options]
  );

  useEffect(() => {
    window.addEventListener("FidesUIShown", handleUIEvent);
    return () => {
      window.removeEventListener("FidesUIShown", handleUIEvent);
    };
  }, [handleUIEvent]);

  return { servedNotices };
};
