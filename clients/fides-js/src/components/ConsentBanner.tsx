import { ComponentChildren, FunctionComponent, h, VNode } from "preact";
import { HTMLAttributes } from "preact/compat";
import { useEffect } from "preact/hooks";

import { A11yDialogAttributes } from "~/lib/a11y-dialog";

import { getConsentContext } from "../lib/consent-context";
import {
  GpcStatus,
  PrivacyExperience,
  PrivacyNoticeWithPreference,
} from "../lib/consent-types";
import { FidesEventTargetType } from "../lib/events";
import { messageExists } from "../lib/i18n";
import { useI18n } from "../lib/i18n/i18n-context";
import { useEvent } from "../lib/providers/event-context";
import CloseButton from "./CloseButton";
import ExperienceDescription from "./ExperienceDescription";
import { GpcBadge } from "./GpcBadge";

interface BannerProps {
  attributes: A11yDialogAttributes;
  dismissable: boolean;
  onOpen: () => void;
  onClose: () => void;
  bannerIsOpen: boolean;
  /**
   * Passing in children components will automatically set the container to be a 2x2 grid,
   * it is up to the child components to specify how they'll be placed within the grid
   * */
  children?: ComponentChildren;
  onVendorPageClick?: () => void;
  renderButtonGroup: () => VNode;
  className?: string;
  isEmbedded: boolean;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  attributes,
  dismissable,
  onOpen,
  onClose,
  bannerIsOpen,
  children,
  onVendorPageClick,
  renderButtonGroup,
  className,
  isEmbedded,
}) => {
  const { container, dialog, title, closeButton } = attributes;
  const { i18n } = useI18n();
  const showGpcBadge = getConsentContext().globalPrivacyControl;
  const { setTrigger } = useEvent();
  useEffect(() => {
    if (bannerIsOpen) {
      onOpen();
    }
  }, [bannerIsOpen, onOpen]);

  // If explicit "banner_description" or "banner_title" values are set, use
  // those to populate the banner. Otherwise, use the generic "description" and
  // "title" values that are shared with the modal component
  const bannerTitle = messageExists(i18n, "exp.banner_title")
    ? i18n.t("exp.banner_title")
    : i18n.t("exp.title");
  const bannerDescription = messageExists(i18n, "exp.banner_description")
    ? i18n.t("exp.banner_description")
    : i18n.t("exp.description");

  const containerClassName = [
    "fides-banner",
    "fides-banner-bottom",
    !bannerIsOpen && "fides-banner-hidden",
    isEmbedded && "fides-embedded",
    className,
  ]
    .filter((c) => typeof c === "string")
    .join(" ");

  let privacyNotices: PrivacyNoticeWithPreference[] | undefined = [];

  if (
    !!(window.Fides?.experience as PrivacyExperience)?.experience_config
      ?.show_layer1_notices &&
    !!(window.Fides?.experience as PrivacyExperience)?.privacy_notices
  ) {
    privacyNotices = (window.Fides?.experience as PrivacyExperience)
      ?.privacy_notices;
  }

  return (
    <div
      className={containerClassName}
      {...(container as Partial<HTMLAttributes<HTMLDivElement>>)}
      id={`${container.id}-container`}
    >
      <div id={container.id}>
        <div
          {...(dialog as Partial<HTMLAttributes<HTMLDivElement>>)}
          id={`${container.id}-inner`}
        >
          <CloseButton
            ariaLabel="Close banner"
            onClick={() => {
              setTrigger({
                type: FidesEventTargetType.BUTTON,
                label: "Close banner",
              });
              closeButton.onClick();
              onClose();
            }}
            hidden={window.Fides?.options?.preventDismissal || !dismissable}
          />
          <div id={`${container.id}-inner-container`}>
            <div className="fides-banner__col">
              <div id="fides-banner-heading">
                <h1
                  className="fides-banner-title"
                  {...(title as Partial<HTMLAttributes<HTMLHeadingElement>>)}
                  id={`${container.id}-title`}
                >
                  {bannerTitle}
                </h1>
                {showGpcBadge && <GpcBadge status={GpcStatus.APPLIED} />}
              </div>
              <div
                id={`${container.id}-description`}
                className="fides-banner-description fides-banner__content"
              >
                <ExperienceDescription
                  description={bannerDescription}
                  onVendorPageClick={onVendorPageClick}
                  allowHTMLDescription={
                    window.Fides?.options?.allowHTMLDescription
                  }
                />
                {!!privacyNotices?.length && (
                  <div
                    id={`${container.id}-notices`}
                    className="fides-banner-notices"
                  >
                    {privacyNotices.map((notice, i) => (
                      <span key={notice.id}>
                        <strong>{notice.name}</strong>
                        {i < privacyNotices!.length - 1 && ", "}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            {children}
          </div>
          {renderButtonGroup()}
        </div>
      </div>
    </div>
  );
};

export default ConsentBanner;
