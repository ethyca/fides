import { h, FunctionComponent } from "preact";
import { ButtonType, ExperienceConfig } from "../lib/consent-types";
import Button from "./Button";
import CloseButton from "./CloseButton";

interface BannerProps {
  experience: ExperienceConfig;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  onManagePreferences: () => void;
  onClose: () => void;
  bannerIsOpen: boolean;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  experience,
  onAcceptAll,
  onRejectAll,
  onManagePreferences,
  onClose,
  bannerIsOpen,
}) => {
  const {
    title = "Manage your consent",
    description = "This website processes your data respectfully, so we require your consent to use cookies.",
    accept_button_label: acceptButtonLabel = "Accept All",
    reject_button_label: rejectButtonLabel = "Reject All",
    privacy_preferences_link_label:
      privacyPreferencesLabel = "Manage preferences",
  } = experience;

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
          <div id="fides-banner-title" className="fides-banner-title">
            {title}
          </div>
          <div
            id="fides-banner-description"
            className="fides-banner-description"
          >
            {description}
          </div>
          <div id="fides-banner-buttons" className="fides-banner-buttons">
            <span className="fides-banner-buttons-left">
              <Button
                buttonType={ButtonType.TERTIARY}
                label={privacyPreferencesLabel}
                onClick={onManagePreferences}
              />
            </span>
            <span className="fides-banner-buttons-right">
              <Button
                buttonType={ButtonType.PRIMARY}
                label={rejectButtonLabel}
                onClick={() => {
                  onRejectAll();
                }}
              />
              <Button
                buttonType={ButtonType.PRIMARY}
                label={acceptButtonLabel}
                onClick={() => {
                  onAcceptAll();
                }}
              />
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConsentBanner;
