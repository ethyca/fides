import { h, FunctionComponent, ComponentChildren } from "preact";
import { getConsentContext } from "../lib/consent-context";
import { ExperienceConfig } from "../lib/consent-types";
import CloseButton from "./CloseButton";
import { GpcBadge } from "./GpcBadge";
import ExperienceDescription from "./ExperienceDescription";

interface BannerProps {
  experience: ExperienceConfig;
  onClose: () => void;
  bannerIsOpen: boolean;
  children: ComponentChildren;
  onVendorPageClick?: () => void;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  experience,
  onClose,
  bannerIsOpen,
  children,
  onVendorPageClick,
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
          <div id="fides-banner-heading">
            <div id="fides-banner-title" className="fides-banner-title">
              {experience.title}
            </div>
            {showGpcBadge ? (
              <GpcBadge
                label="Global Privacy Control Signal"
                status="detected"
              />
            ) : null}
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
          {children}
        </div>
      </div>
    </div>
  );
};

export default ConsentBanner;
