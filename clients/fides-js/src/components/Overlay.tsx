/* eslint-disable no-nested-ternary */
import "./fides.css";

import { FunctionComponent, h, VNode } from "preact";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "preact/hooks";

import { useA11yDialog } from "../lib/a11y-dialog";
import { FIDES_OVERLAY_WRAPPER } from "../lib/consent-constants";
import {
  FidesCookie,
  FidesInitOptions,
  NoticeConsent,
  PrivacyExperience,
  PrivacyExperienceMinimal,
} from "../lib/consent-types";
import { defaultShowModal, shouldResurfaceBanner } from "../lib/consent-utils";
import { dispatchFidesEvent } from "../lib/events";
import {
  useElementById,
  useElementsByQuerySelector,
  useHasMounted,
} from "../lib/hooks";
import { useI18n } from "../lib/i18n/i18n-context";
import { blockPageScrolling, unblockPageScrolling } from "../lib/ui-utils";
import ConsentContent from "./ConsentContent";
import ConsentModal from "./ConsentModal";

interface RenderBannerProps {
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
  onOpen: () => void;
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
  const { i18n } = useI18n();
  const delayBannerMilliseconds = 100;
  const hasMounted = useHasMounted();

  // Forces Modal Link to have an ID.
  const modalLinkId = options.modalLinkId || "fides-modal-link";
  const modalLinkByIdIsDisabled =
    !experience ||
    !!options.fidesEmbed ||
    // This can't ever be true?
    options.modalLinkId === "";
  const modalLink = useElementById(modalLinkId, modalLinkByIdIsDisabled);
  const modalLinkRef = useRef<HTMLElement[]>([]);

  const modalLinkByQuerySelectorIsDisabled =
    !experience || !!options.fidesEmbed || !options.modalLinkQuerySelector;
  const modalLinkByQuerySelector = options.modalLinkQuerySelector;
  const modalLinks = useElementsByQuerySelector(
    modalLinkByQuerySelector ?? "",
    modalLinkByQuerySelectorIsDisabled,
  );

  const modalLinkElements = useMemo(() => {
    const elements = [...modalLinks];
    if (modalLink) {
      elements.push(modalLink);
    }
    return elements;
  }, [modalLinks, modalLink]);

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
      dispatchFidesEvent("FidesModalClosed", cookie, options.debug, { saved });
      if (!saved) {
        onDismiss();
      }
    },
    [cookie, onDismiss, options.debug],
  );

  const { instance, attributes } = useA11yDialog({
    id: "fides-modal",
    role: "alertdialog",
    title: i18n.t("exp.title"),
    onClose: () => {
      dispatchCloseEvent({ saved: false });
    },
  });

  const handleOpenModal = useCallback(() => {
    if (options.fidesEmbed) {
      setBannerIsOpen(false);
    } else if (instance) {
      setBannerIsOpen(false);
      instance.show();
      onOpen();
    }
  }, [instance, onOpen, options]);

  const handleCloseModalAfterSave = useCallback(() => {
    if (instance && !options.fidesEmbed) {
      instance.hide();
      dispatchCloseEvent({ saved: true });
    }
  }, [instance, dispatchCloseEvent, options.fidesEmbed]);

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
      window.Fides.showModal = handleOpenModal;
    }
    return () => {
      window.Fides.showModal = defaultShowModal;
    };
  }, [experience, handleOpenModal, options.fidesEmbed]);

  useEffect(() => {
    if (modalLinkByIdIsDisabled && modalLinkByQuerySelectorIsDisabled) {
      fidesDebugger("Modal Link is disabled for this experience.");
    }
  }, [modalLinkByQuerySelectorIsDisabled, modalLinkByIdIsDisabled]);

  useEffect(() => {
    document.body.classList.add("fides-overlay-modal-link-shown");
    // If empty string is explicitly set, do not attempt to bind the modal link to the click handler.
    // developers using `Fides.showModal();` can use this to prevent polling for the modal link. Developers should always be able to rely on the .fides-overlay-modal-link-shown classname to show their custom modal link.

    if (modalLinks.length > 0) {
      fidesDebugger(
        "Modal link elements found, updating them to show and trigger modal on click.",
      );
      modalLinkRef.current = modalLinkElements;
      modalLinkRef.current.forEach((element) =>
        element.addEventListener("click", window.Fides.showModal),
      );
      // show the modal link in the DOM
      modalLinkRef.current.forEach((element) =>
        element.classList.add("fides-modal-link-shown"),
      );
    } else {
      fidesDebugger(`Searching for Modal link element #${modalLinkId}...`);
      if (modalLinkByQuerySelector) {
        fidesDebugger(
          `Searching for Modal link elements ${modalLinkByQuerySelector}...`,
        );
      }
    }

    return () => {
      if (modalLinkRef.current) {
        modalLinkRef.current.forEach((element) =>
          element.removeEventListener("click", window.Fides.showModal),
        );
      }
    };
  }, [
    modalLink,
    modalLinkByQuerySelector,
    modalLinkByIdIsDisabled,
    modalLinkElements,
    modalLinkId,
    modalLinks,
  ]);

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
            titleProps={attributes.title}
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
          attributes={attributes}
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
