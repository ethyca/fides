import { h, FunctionComponent, VNode } from "preact";
import { useEffect, useState, useCallback, useMemo } from "preact/hooks";
import {
  FidesOptions,
  PrivacyExperience,
  ServingComponent,
} from "../lib/consent-types";

import { debugLog, hasActionNeededNotices } from "../lib/consent-utils";

import { useA11yDialog } from "../lib/a11y-dialog";
import ConsentModal from "./ConsentModal";
import { useHasMounted } from "../lib/hooks";
import { dispatchFidesEvent } from "../lib/events";
import {
  FidesCookie,
  getOrMakeFidesCookie,
  isNewFidesCookie,
} from "../lib/cookie";

interface RenderBannerProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  onManagePreferencesClick: () => void;
}

interface RenderModalContent {
  onClose: () => void;
}

interface Props {
  options: FidesOptions;
  experience: PrivacyExperience;
  cookie: FidesCookie;
  renderBanner: (props: RenderBannerProps) => VNode | null;
  renderModalContent: (props: RenderModalContent) => VNode;
}

/**
 * Overlay doesn't always have the most up to date cookie. For the most part,
 * we prefer the cookie on the DOM, except when that cookie doesn't exist yet,
 * in which case we want the cookie object that was passed into this component.
 */
const getLatestCookie = (cookieFromParam: FidesCookie) => {
  const latestCookie = getOrMakeFidesCookie();
  return isNewFidesCookie(latestCookie) ? cookieFromParam : latestCookie;
};

const Overlay: FunctionComponent<Props> = ({
  experience,
  options,
  cookie,
  renderBanner,
  renderModalContent,
}) => {
  const delayBannerMilliseconds = 100;
  const delayModalLinkMilliseconds = 200;
  const hasMounted = useHasMounted();
  const [bannerIsOpen, setBannerIsOpen] = useState(false);

  const dispatchCloseEvent = useCallback(() => {
    dispatchFidesEvent(
      "FidesModalClosed",
      getLatestCookie(cookie),
      options.debug
    );
  }, [cookie, options.debug]);

  const { instance, attributes } = useA11yDialog({
    id: "fides-modal",
    role: "dialog",
    title: experience?.experience_config?.title || "",
    onClose: dispatchCloseEvent,
  });

  const handleOpenModal = useCallback(() => {
    if (instance) {
      instance.show();
      dispatchFidesEvent(
        "FidesUIShown",
        getLatestCookie(cookie),
        options.debug,
        {
          servingComponent: ServingComponent.OVERLAY,
        }
      );
    }
  }, [instance, cookie, options.debug]);

  const handleCloseModal = useCallback(() => {
    if (instance) {
      instance.hide();
      dispatchCloseEvent();
    }
  }, [instance, dispatchCloseEvent]);

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
    () => experience.show_banner && hasActionNeededNotices(experience),
    [experience]
  );

  useEffect(() => {
    const eventCookie = getLatestCookie(cookie);
    if (showBanner && bannerIsOpen) {
      dispatchFidesEvent("FidesUIShown", eventCookie, options.debug, {
        servingComponent: ServingComponent.BANNER,
      });
    }
  }, [showBanner, cookie, options.debug, bannerIsOpen]);

  useEffect(() => {
    const cssUrl = new URL("fides.css", options.privacyCenterUrl);
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = cssUrl.href;
    document.head.appendChild(link);
  }, [options.privacyCenterUrl]);

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
      <ConsentModal
        attributes={attributes}
        experience={experience.experience_config}
      >
        {renderModalContent({ onClose: handleCloseModal })}
      </ConsentModal>
    </div>
  );
};

export default Overlay;
