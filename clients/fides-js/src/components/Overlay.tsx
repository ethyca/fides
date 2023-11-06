import { h, FunctionComponent, VNode } from "preact";
import { useEffect, useState, useCallback, useMemo } from "preact/hooks";
import { FidesOptions, PrivacyExperience } from "../lib/consent-types";

import { debugLog, shouldResurfaceConsent } from "../lib/consent-utils";

import "./fides.css";
import { useA11yDialog } from "../lib/a11y-dialog";
import ConsentModal from "./ConsentModal";
import { useHasMounted } from "../lib/hooks";
import { dispatchFidesEvent } from "../lib/events";
import { FidesCookie } from "../lib/cookie";
import ConsentContent from "./ConsentContent";

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
  onOpen: () => void;
  renderBanner: (props: RenderBannerProps) => VNode | null;
  renderModalContent: () => VNode;
  renderModalFooter: (props: RenderModalFooter) => VNode;
  onVendorPageClick?: () => void;
}

const Overlay: FunctionComponent<Props> = ({
  experience,
  options,
  cookie,
  onOpen,
  renderBanner,
  renderModalContent,
  renderModalFooter,
  onVendorPageClick,
}) => {
  const delayBannerMilliseconds = 100;
  const delayModalLinkMilliseconds = 200;
  const hasMounted = useHasMounted();
  const [bannerIsOpen, setBannerIsOpen] = useState(false);

  const dispatchCloseEvent = useCallback(() => {
    dispatchFidesEvent("FidesModalClosed", cookie, options.debug);
  }, [cookie, options.debug]);

  const { instance, attributes } = useA11yDialog({
    id: "fides-modal",
    role: "alertdialog",
    title: experience?.experience_config?.title || "",
    onClose: dispatchCloseEvent,
  });

  const handleOpenModal = useCallback(() => {
    if (instance) {
      instance.show();
      onOpen();
    }
  }, [instance, onOpen]);

  const handleCloseModal = useCallback(() => {
    if (instance && !options.fidesEmbed) {
      instance.hide();
      dispatchCloseEvent();
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
    // use a delay to ensure that link exists in the DOM
    const delayModalLinkBinding = setTimeout(() => {
      const modalLinkId = options.modalLinkId || "fides-modal-link";
      const modalLinkEl = document.getElementById(modalLinkId);
      if (modalLinkEl) {
        debugLog(
          options.debug,
          "Modal link element found, updating it to show and trigger modal on click."
        );
        // Update modal link to trigger modal on click
        const modalLink = modalLinkEl;
        modalLink.onclick = () => {
          handleOpenModal();
          setBannerIsOpen(false);
        };
        // Update to show the pre-existing modal link in the DOM
        modalLink.classList.add("fides-modal-link-shown");
      } else {
        debugLog(options.debug, "Modal link element not found.");
      }
    }, delayModalLinkMilliseconds);
    return () => clearTimeout(delayModalLinkBinding);
  }, [options.modalLinkId, options.debug, handleOpenModal]);

  const showBanner = useMemo(
    () =>
      !options.fidesDisableBanner &&
      experience.show_banner &&
      shouldResurfaceConsent(experience, cookie) &&
      !options.fidesEmbed,
    [experience, options, cookie]
  );

  const handleManagePreferencesClick = (): void => {
    handleOpenModal();
    setBannerIsOpen(false);
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
              onClose: handleCloseModal,
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
              onClose: handleCloseModal,
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
