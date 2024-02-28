import { h, FunctionComponent, ComponentChildren, VNode } from "preact";
import { useState, useEffect } from "preact/hooks";
import { getConsentContext } from "../lib/consent-context";
import { ExperienceConfig } from "../lib/consent-types";
import CloseButton from "./CloseButton";
import { GpcBadge } from "./GpcBadge";
import ExperienceDescription from "./ExperienceDescription";
import type { I18n } from "../lib/i18n";

interface ButtonGroupProps {
  isMobile: boolean;
}

interface BannerProps {
  experience: ExperienceConfig;
  i18n: I18n;
  onOpen: () => void;
  onClose: () => void;
  bannerIsOpen: boolean;
  /**
   * Passing in children components will automatically set the container to be a 2x2 grid,
   * it is up to the child components to specify how they'll be placed within the grid
   * */
  children?: ComponentChildren;
  onVendorPageClick?: () => void;
  renderButtonGroup: (props: ButtonGroupProps) => VNode;
  className?: string;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  experience,
  i18n,
  onOpen,
  onClose,
  bannerIsOpen,
  children,
  onVendorPageClick,
  renderButtonGroup,
  className,
}) => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    window.addEventListener("resize", handleResize);

    // Cleanup the event listener on component unmount
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const showGpcBadge = getConsentContext().globalPrivacyControl;

  useEffect(() => {
    if (bannerIsOpen) {
      onOpen();
    }
  }, [bannerIsOpen, onOpen]);

  // If explicit "banner_description" or "banner_title" values are set, use
  // those to populate the banner. Otherwise, use the generic "description" and
  // "title" values that are shared with the modal component
  // TODO (PROD-1597): ensure that null banner_title / banner_description is handled...
  const bannerTitle = i18n.t("exp.banner_title") || i18n.t("exp.title");
  const bannerDescription = i18n.t("exp.banner_description") || i18n.t("exp.description");

  return (
    <div
      id="fides-banner-container"
      className={`fides-banner fides-banner-bottom 
        ${bannerIsOpen ? "" : "fides-banner-hidden"} 
        ${className || ""}`}
    >
      <div id="fides-banner">
        <div id="fides-banner-inner">
          <CloseButton
            ariaLabel="Close banner"
            onClick={onClose}
            hidden={window.Fides?.options?.preventDismissal}
          />
          <div
            id="fides-banner-inner-container"
            style={{
              gridTemplateColumns: children ? "1fr 1fr" : "1fr",
            }}
          >
            <div id="fides-banner-inner-description">
              <div id="fides-banner-heading">
                <div id="fides-banner-title" className="fides-banner-title">
                  {bannerTitle}
                </div>
                {showGpcBadge && (
                  <GpcBadge
                    label="Global Privacy Control Signal"
                    status="detected"
                  />
                )}
              </div>
              <div
                id="fides-banner-description"
                className="fides-banner-description"
              >
                <ExperienceDescription
                  description={bannerDescription}
                  onVendorPageClick={onVendorPageClick}
                  allowHTMLDescription={
                    window.Fides?.options?.allowHTMLDescription
                  }
                />
              </div>
            </div>
            {children}
            {!isMobile && renderButtonGroup({ isMobile })}
          </div>
          {isMobile && renderButtonGroup({ isMobile })}
        </div>
      </div>
    </div>
  );
};

export default ConsentBanner;
