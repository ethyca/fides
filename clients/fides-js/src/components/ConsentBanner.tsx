import { h, FunctionComponent } from "preact";
import { useState, useEffect } from "preact/hooks";
import { ButtonType, ExperienceConfig } from "../lib/consent-types";
import Button from "./Button";

interface BannerProps {
  experience: ExperienceConfig;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  waitBeforeShow?: number;
  managePreferencesLabel?: string;
  onOpenModal: () => void;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  experience,
  onAcceptAll,
  onRejectAll,
  waitBeforeShow,
  onOpenModal,
}) => {
  const [isShown, setIsShown] = useState(false);

  const {
    title = "Manage your consent",
    description = "This website processes your data respectfully, so we require your consent to use cookies.",
    accept_button_label: acceptButtonLabel = "Accept All",
    reject_button_label: rejectButtonLabel = "Reject All",
    privacy_preferences_link_label:
      privacyPreferencesLabel = "Manage preferences",
  } = experience;

  useEffect(() => {
    const delayBanner = setTimeout(() => {
      setIsShown(true);
    }, waitBeforeShow);
    return () => clearTimeout(delayBanner);
  }, [setIsShown, waitBeforeShow]);

  const handleManagePreferencesClick = (): void => {
    onOpenModal();
    setIsShown(false);
  };

  return (
    <div
      id="fides-consent-banner"
      className={`fides-consent-banner fides-consent-banner-bottom ${
        isShown ? "" : "fides-consent-banner-hidden"
      } `}
    >
      <div id="fides-consent-banner-inner">
        <div
          id="fides-consent-banner-title"
          className="fides-consent-banner-title"
        >
          {title}
        </div>
        <div
          id="fides-consent-banner-description"
          className="fides-consent-banner-description"
        >
          {description}
        </div>
        <div
          id="fides-consent-banner-buttons"
          className="fides-consent-banner-buttons"
        >
          <span className="fides-consent-banner-buttons-left">
            <Button
              buttonType={ButtonType.TERTIARY}
              label={privacyPreferencesLabel}
              onClick={handleManagePreferencesClick}
            />
          </span>
          <span className="fides-consent-banner-buttons-right">
            <Button
              buttonType={ButtonType.PRIMARY}
              label={rejectButtonLabel}
              onClick={() => {
                onRejectAll();
                setIsShown(false);
              }}
            />
            <Button
              buttonType={ButtonType.PRIMARY}
              label={acceptButtonLabel}
              onClick={() => {
                onAcceptAll();
                setIsShown(false);
              }}
            />
          </span>
        </div>
      </div>
    </div>
  );
};

export default ConsentBanner;
