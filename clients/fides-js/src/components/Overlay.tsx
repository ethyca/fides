import { h, FunctionComponent, VNode } from "preact";
import {
  useEffect,
  useState,
  useCallback,
  useMemo,
  useRef,
} from "preact/hooks";
import {
  CookieKeyConsent,
  FidesCookie,
  FidesOptions,
  PrivacyExperience,
} from "../lib/consent-types";

import { debugLog, shouldResurfaceConsent } from "../lib/consent-utils";

import "./fides.css";
import { useA11yDialog } from "../lib/a11y-dialog";
import ConsentModal from "./ConsentModal";
import { useHasMounted } from "../lib/hooks";
import { dispatchFidesEvent } from "../lib/events";
import ConsentContent from "./ConsentContent";
import { defaultShowModal } from "../fides";

interface RenderBannerProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  onManagePreferencesClick: () => void;
}
interface RenderModalFooter {
  onClose: () => void;
  isMobile: boolean;
}

interface Props {
  options: FidesOptions;
  experience: PrivacyExperience;
  cookie: FidesCookie;
  savedConsent: CookieKeyConsent;
  onOpen: () => void;
  onDismiss: () => void;
  renderBanner: (props: RenderBannerProps) => VNode | null;
  renderModalContent: () => VNode;
  renderModalFooter: (props: RenderModalFooter) => VNode;
  onVendorPageClick?: () => void;
}

const Overlay: FunctionComponent<Props> = ({
  experience,
  options,
  cookie,
  savedConsent,
  onOpen,
  onDismiss,
  renderBanner,
  renderModalContent,
  renderModalFooter,
  onVendorPageClick,
}) => {
  const delayBannerMilliseconds = 100;
  const delayModalLinkMilliseconds = 200;
  const hasMounted = useHasMounted();
  const [bannerIsOpen, setBannerIsOpen] = useState(false);
  const modalLinkRef = useRef<HTMLElement | null>(null);

  const dispatchCloseEvent = useCallback(
    ({ saved = false }: { saved?: boolean }) => {
      dispatchFidesEvent("FidesModalClosed", cookie, options.debug, { saved });
      if (!saved) {
        onDismiss();
      }
    },
    [cookie, onDismiss, options.debug]
  );

  const { instance, attributes } = useA11yDialog({
    id: "fides-modal",
    role: "alertdialog",
    title: experience?.experience_config?.title || "",
    onClose: () => {
      dispatchCloseEvent({ saved: false });
    },
  });

  const handleOpenModal = useCallback(() => {
    if (instance) {
      setBannerIsOpen(false);
      instance.show();
      onOpen();
    }
  }, [instance, onOpen]);

  const handleCloseModalAfterSave = useCallback(() => {
    if (instance && !options.fidesEmbed) {
      instance.hide();
      dispatchCloseEvent({ saved: true });
    }
  }, [instance, dispatchCloseEvent, options.fidesEmbed]);

  useEffect(() => {
    if (options.fidesEmbed) {
      onOpen();
    }
  }, [options, onOpen]);

  useEffect(() => {
    const delayBanner = setTimeout(() => {
      setBannerIsOpen(true);
    }, delayBannerMilliseconds);
    return () => clearTimeout(delayBanner);
  }, [setBannerIsOpen]);

  useEffect(() => {
    window.Fides.showModal = handleOpenModal;
    document.body.classList.add("fides-overlay-modal-link-shown");
    // use a delay to ensure that link exists in the DOM
    const delayModalLinkBinding = setTimeout(() => {
      const modalLinkId = options.modalLinkId || "fides-modal-link";
      const modalLinkEl = document.getElementById(modalLinkId);
      if (modalLinkEl) {
        debugLog(
          options.debug,
          "Modal link element found, updating it to show and trigger modal on click."
        );
        modalLinkRef.current = modalLinkEl;
        modalLinkRef.current.addEventListener("click", window.Fides.showModal);
        // Update to show the pre-existing modal link in the DOM
        modalLinkRef.current.classList.add("fides-modal-link-shown");
      } else {
        debugLog(options.debug, "Modal link element not found.");
      }
    }, delayModalLinkMilliseconds);
    return () => {
      clearTimeout(delayModalLinkBinding);
      if (modalLinkRef.current) {
        modalLinkRef.current.removeEventListener(
          "click",
          window.Fides.showModal
        );
      }
      window.Fides.showModal = defaultShowModal;
    };
  }, [options.modalLinkId, options.debug, handleOpenModal]);

  const showBanner = useMemo(
    () =>
      !options.fidesDisableBanner &&
      experience.show_banner &&
      shouldResurfaceConsent(experience, cookie, savedConsent) &&
      !options.fidesEmbed,
    [cookie, savedConsent, experience, options]
  );

  /* eslint-disable-next-line no-console -- TODO(PROD-1780) remove log */
  console.warn("renderOverlay showBanner = ", showBanner);

  const handleManagePreferencesClick = (): void => {
    handleOpenModal();
  };

  if (!hasMounted) {
    return null;
  }

  if (!experience.experience_config) {
    debugLog(options.debug, "No experience config found");
    return null;
  }

  return (
    <div>
      {showBanner && bannerIsOpen && window.Fides.options.preventDismissal && (
        <div className="fides-modal-overlay" />
      )}
      {showBanner
        ? renderBanner({
            isOpen: bannerIsOpen,
            onClose: () => {
              setBannerIsOpen(false);
            },
            onSave: () => {
              setBannerIsOpen(false);
            },
            onManagePreferencesClick: handleManagePreferencesClick,
          })
        : null}
      {options.fidesEmbed ? (
        <ConsentContent
          title={attributes.title}
          className="fides-embed"
          experience={experience.experience_config}
          renderModalFooter={() =>
            renderModalFooter({
              onClose: handleCloseModalAfterSave,
              isMobile: false,
            })
          }
        >
          {renderModalContent()}
        </ConsentContent>
      ) : (
        <ConsentModal
          attributes={attributes}
          experience={experience.experience_config}
          onVendorPageClick={onVendorPageClick}
          renderModalFooter={() =>
            renderModalFooter({
              onClose: handleCloseModalAfterSave,
              isMobile: false,
            })
          }
          renderModalContent={renderModalContent}
        />
      )}
    </div>
  );
};

export default Overlay;
