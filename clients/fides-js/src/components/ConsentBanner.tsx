import { h, FunctionComponent, ComponentChildren, VNode } from "preact";
import { getConsentContext } from "../lib/consent-context";
import { ExperienceConfig } from "../lib/consent-types";
import CloseButton from "./CloseButton";
import { GpcBadge } from "./GpcBadge";
import ExperienceDescription from "./ExperienceDescription";

interface BannerProps {
  experience: ExperienceConfig;
  onClose: () => void;
  bannerIsOpen: boolean;
  /**
   * Passing in children components will automatically set the container to be a 2x2 grid,
   * it is up to the child components to specify how they'll be placed within the grid
   * */
  children?: ComponentChildren;
  onVendorPageClick?: () => void;
  buttonGroup: VNode;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  experience,
  onClose,
  bannerIsOpen,
  children,
  onVendorPageClick,
  buttonGroup,
}) => {
  const showGpcBadge = getConsentContext().globalPrivacyControl;
  return (
    <div
      id="fides-banner-container"
      className={`fides-banner fides-banner-bottom ${
        bannerIsOpen ? "" : "fides-banner-hidden"
      } `}
    >
      <div id="fides-banner">
        <div id="fides-banner-inner">
          <CloseButton ariaLabel="Close banner" onClick={onClose} />
          <div
            id="fides-banner-inner-container"
            style={{
              gridTemplateColumns: children ? "1fr 1fr" : "1fr",
            }}
          >
            <div id="fides-banner-inner-description">
              <div id="fides-banner-heading">
                <div id="fides-banner-title" className="fides-banner-title">
                  {experience.title}
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
                  description={experience.description}
                  onVendorPageClick={onVendorPageClick}
                />
              </div>
            </div>
            {children}
            {buttonGroup}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConsentBanner;
