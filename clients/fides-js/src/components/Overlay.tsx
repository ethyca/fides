/* eslint-disable no-nested-ternary */
import "./fides.css";

import { FunctionComponent, VNode } from "preact";
import { useCallback, useEffect, useRef, useState } from "preact/hooks";

import { A11yDialogAttributes, useA11yDialog } from "../lib/a11y-dialog";
import { FIDES_OVERLAY_WRAPPER } from "../lib/consent-constants";
import {
  FidesCookie,
  FidesInitOptions,
  NoticeConsent,
  PrivacyExperience,
  PrivacyExperienceMinimal,
} from "../lib/consent-types";
import { defaultShowModal, shouldResurfaceBanner } from "../lib/consent-utils";
import { FidesEventOrigin } from "../lib/events";
import { useElementById, useHasMounted } from "../lib/hooks";
import { useEvent } from "../lib/providers/event-context";
import { blockPageScrolling, unblockPageScrolling } from "../lib/ui-utils";
import ConsentContent from "./ConsentContent";
import ConsentModal from "./ConsentModal";

interface RenderBannerProps {
  attributes: A11yDialogAttributes;
  isOpen: boolean;
  isEmbedded: boolean;
  onClose: () => void;
  onManagePreferencesClick: () => void;
}

interface RenderModalFooterProps {
  onClose: () => void;
  isMobile: boolean;
}

interface Props {
  options: FidesInitOptions;
  experience: PrivacyExperience | PrivacyExperienceMinimal;
  cookie: FidesCookie;
  savedConsent: NoticeConsent;
  onOpen: (origin?: string) => void;
  onDismiss: () => void;
  renderBanner: (props: RenderBannerProps) => VNode | null;
  renderModalContent?: () => VNode | null;
  renderModalFooter?: (props: RenderModalFooterProps) => VNode | null;
  onVendorPageClick?: () => void;
  isUiBlocking: boolean;
}

const Overlay: FunctionComponent<Props> = ({
  options,
  experience,
  cookie,
  savedConsent,
  onOpen,
  onDismiss,
  renderBanner,
  renderModalContent,
  renderModalFooter,
  onVendorPageClick,
  isUiBlocking,
}) => {
  const { setServingComponent, dispatchFidesEventAndClearTrigger } = useEvent();
  const delayBannerMilliseconds = 100;
  const hasMounted = useHasMounted();
  const modalLinkId = options.modalLinkId || "fides-modal-link";
  const modalLinkIsDisabled =
    !experience || !!options.fidesEmbed || options.modalLinkId === "";
  const modalLink = useElementById(modalLinkId, modalLinkIsDisabled);
  const modalLinkRef = useRef<HTMLElement | null>(null);
  const [disableBanner, setDisableBanner] = useState<boolean | null>(null);

  useEffect(() => {
    if (disableBanner === null) {
      // We check for disableBanner being `null` so that this only ever gets set
      // during initialization and not with every change to the cookie/consent.
      // This is also why exaustive-deps is being ignored below.
      setDisableBanner(
        !shouldResurfaceBanner(experience, cookie, savedConsent, options),
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [disableBanner]);

  // When fidesEmbed is enabled, this should be set immediately (don't wait for css animation support)
  const [bannerIsOpen, setBannerIsOpen] = useState(
    options.fidesEmbed
      ? shouldResurfaceBanner(experience, cookie, savedConsent, options)
      : false,
  );

  useEffect(() => {
    if (isUiBlocking && bannerIsOpen) {
      blockPageScrolling();
    } else {
      unblockPageScrolling();
    }

    return () => {
      unblockPageScrolling();
    };
  }, [isUiBlocking, bannerIsOpen]);

  const dispatchCloseEvent = useCallback(
    ({ saved = false }: { saved?: boolean }) => {
      if (!saved) {
        onDismiss();
      }
      dispatchFidesEventAndClearTrigger("FidesModalClosed", cookie, { saved });
      setServingComponent(undefined);
    },
    [dispatchFidesEventAndClearTrigger, cookie, onDismiss, setServingComponent],
  );

  const { instance: modalDialogInstance, attributes: modalDialogAttributes } =
    useA11yDialog({
      id: "fides-modal",
      onClose: () => {
        dispatchCloseEvent({ saved: false });
      },
    });

  useEffect(() => {
    if (modalDialogInstance) {
      modalDialogInstance
        .on("show", () => {
          document.documentElement.style.overflowY = "hidden";
        })
        .on("hide", () => {
          document.documentElement.style.overflowY = "";
        });
    }
  }, [modalDialogInstance]);

  const { attributes: bannerDialogAttributes } = useA11yDialog({
    id: "fides-banner",
    ariaHidden: !bannerIsOpen && !options.fidesEmbed,
    onClose: () => {
      setBannerIsOpen(false);
    },
  });

  const handleOpenModal = useCallback(
    (origin = FidesEventOrigin.FIDES) => {
      if (options.fidesEmbed) {
        setBannerIsOpen(false);
      } else if (modalDialogInstance) {
        setBannerIsOpen(false);
        modalDialogInstance.show();
        onOpen(origin);
      }
    },
    [modalDialogInstance, onOpen, options],
  );

  const handleCloseModalAfterSave = useCallback(() => {
    if (modalDialogInstance && !options.fidesEmbed) {
      modalDialogInstance.hide();
      dispatchCloseEvent({ saved: true });
    }
  }, [modalDialogInstance, dispatchCloseEvent, options.fidesEmbed]);

  useEffect(() => {
    if (options.fidesEmbed && !bannerIsOpen) {
      onOpen();
    }
  }, [options, onOpen, bannerIsOpen]);

  // The delay is needed for the banner CSS animation
  useEffect(() => {
    const delayBanner = setTimeout(() => {
      if (!disableBanner) {
        setBannerIsOpen(true);
      }
    }, delayBannerMilliseconds);
    return () => clearTimeout(delayBanner);
  }, [disableBanner, setBannerIsOpen]);

  useEffect(() => {
    if (!!experience && !options.fidesEmbed) {
      window.Fides.showModal = () => {
        handleOpenModal(FidesEventOrigin.EXTERNAL);
      };
    }
    return () => {
      window.Fides.showModal = defaultShowModal;
    };
  }, [experience, handleOpenModal, options.fidesEmbed]);

  useEffect(() => {
    document.body.classList.add("fides-overlay-modal-link-shown");
    // If empty string is explicitly set, do not attempt to bind the modal link to the click handler.
    // developers using `Fides.showModal();` can use this to prevent polling for the modal link. Developers should always be able to rely on the .fides-overlay-modal-link-shown classname to show their custom modal link.
    if (!modalLinkIsDisabled) {
      if (modalLink) {
        fidesDebugger(
          "Modal link element found, updating it to show and trigger modal on click.",
        );
        modalLinkRef.current = modalLink;
        modalLinkRef.current.addEventListener("click", window.Fides.showModal);
        // show the modal link in the DOM
        modalLinkRef.current.classList.add("fides-modal-link-shown");
      } else {
        fidesDebugger(`Searching for Modal link element #${modalLinkId}...`);
      }
    } else {
      fidesDebugger("Modal Link is disabled for this experience.");
    }
    return () => {
      if (modalLinkRef.current) {
        modalLinkRef.current.removeEventListener(
          "click",
          window.Fides.showModal,
        );
      }
    };
  }, [modalLink, modalLinkIsDisabled, modalLinkId]);

  const handleManagePreferencesClick = (): void => {
    handleOpenModal();
  };

  if (!hasMounted) {
    return null;
  }

  if (!experience.experience_config) {
    fidesDebugger("No experience config found");
    return null;
  }

  return (
    <div id={FIDES_OVERLAY_WRAPPER} tabIndex={-1}>
      {!disableBanner && bannerIsOpen && isUiBlocking && (
        <div className="fides-modal-overlay" />
      )}
      {options.fidesEmbed ? (
        bannerIsOpen || !renderModalContent || !renderModalFooter ? null : (
          <ConsentContent
            titleProps={modalDialogAttributes.title}
            renderModalFooter={() =>
              renderModalFooter({
                onClose: handleCloseModalAfterSave,
                isMobile: false,
              })
            }
            onVendorPageClick={onVendorPageClick}
          >
            {renderModalContent()}
          </ConsentContent>
        )
      ) : (
        /* If the modal is not going to be embedded, we at least need to instantiate the wrapper
         * before the footer and content are available so that it can be opened while those render.
         * Otherwise a race condition can cause problems with the following scenario:
         * button click too early -> button has spinner -> experience loads -> modal opener called.
         * This scenario exists today for TCF Minimal experience where banner appears before
         * full experience (and therefore the modal) is ready.
         */
        <ConsentModal
          attributes={modalDialogAttributes}
          dismissable={experience.experience_config.dismissable}
          onVendorPageClick={onVendorPageClick}
          renderModalFooter={() =>
            renderModalFooter
              ? renderModalFooter({
                  onClose: handleCloseModalAfterSave,
                  isMobile: false,
                })
              : null
          }
        >
          {renderModalContent && renderModalContent()}
        </ConsentModal>
      )}
      {!disableBanner &&
        renderBanner({
          attributes: bannerDialogAttributes,
          isOpen: bannerIsOpen,
          isEmbedded: options.fidesEmbed,
          onClose: () => {
            setBannerIsOpen(false);
          },
          onManagePreferencesClick: handleManagePreferencesClick,
        })}
    </div>
  );
};

export default Overlay;
