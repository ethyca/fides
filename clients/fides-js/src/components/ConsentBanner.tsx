import { h, FunctionComponent, VNode } from "preact";
import { ExperienceConfig, GpcStatus } from "../lib/consent-types";
import CloseButton from "./CloseButton";
import { GpcBadge } from "./GpcBadge";

interface BannerProps {
  experience: ExperienceConfig;
  onClose: () => void;
  bannerIsOpen: boolean;
  buttonGroup: VNode;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  experience,
  buttonGroup,
  onClose,
  bannerIsOpen,
}) => {
  const gpcStatus = GpcStatus.APPLIED;
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
            <GpcBadge status={gpcStatus} />
          </div>
          <div
            id="fides-banner-description"
            className="fides-banner-description"
          >
            {experience.description}
          </div>
          {buttonGroup}
        </div>
      </div>
    </div>
  );
};

export default ConsentBanner;
