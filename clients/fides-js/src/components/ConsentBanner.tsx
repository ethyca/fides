import { ComponentChildren, FunctionComponent, h, VNode } from "preact";
import { useEffect } from "preact/hooks";

import { getConsentContext } from "../lib/consent-context";
import {
  GpcStatus,
  PrivacyExperience,
  PrivacyNoticeWithPreference,
} from "../lib/consent-types";
import { messageExists } from "../lib/i18n";
import { useI18n } from "../lib/i18n/i18n-context";
import CloseButton from "./CloseButton";
import ExperienceDescription from "./ExperienceDescription";
import { GpcBadge } from "./GpcBadge";

interface BannerProps {
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
  const { i18n } = useI18n();
  const showGpcBadge = getConsentContext().globalPrivacyControl;

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
    <div id="fides-banner-container" className={containerClassName}>
      <div id="fides-banner">
        <div id="fides-banner-inner">
          <CloseButton
            ariaLabel="Close banner"
            onClick={onClose}
            hidden={window.Fides?.options?.preventDismissal || !dismissable}
          />
          <div id="fides-banner-inner-container">
            <div className="fides-banner__col">
              <div id="fides-banner-heading">
                <h1 id="fides-banner-title" className="fides-banner-title">
                  {bannerTitle}
                </h1>
                {showGpcBadge && <GpcBadge status={GpcStatus.APPLIED} />}
              </div>
              <div
                id="fides-banner-description"
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
                    id="fides-banner-notices"
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
