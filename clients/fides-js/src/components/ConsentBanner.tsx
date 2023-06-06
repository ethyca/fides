import { h, FunctionComponent } from "preact";
import { useEffect, StateUpdater } from "preact/hooks";
import { ButtonType, ExperienceConfig } from "../lib/consent-types";
import Button from "./Button";
import { useHasMounted } from "../lib/hooks";

interface BannerProps {
  experience: ExperienceConfig;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  waitBeforeShow?: number;
  managePreferencesLabel?: string;
  onOpenModal: () => void;
  bannerIsOpen: boolean;
  setBannerIsOpen: StateUpdater<boolean>;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  experience,
  onAcceptAll,
  onRejectAll,
  waitBeforeShow,
  onOpenModal,
  bannerIsOpen,
  setBannerIsOpen,
}) => {
  const hasMounted = useHasMounted();
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
      setBannerIsOpen(true);
    }, waitBeforeShow);
    return () => clearTimeout(delayBanner);
  }, [setBannerIsOpen, waitBeforeShow]);

  const handleManagePreferencesClick = (): void => {
    onOpenModal();
    setBannerIsOpen(false);
  };

  if (!hasMounted) {
    return null;
  }

  return (
    <div
      id="fides-banner-container"
      className={`fides-banner fides-banner-bottom ${
        bannerIsOpen ? "" : "fides-banner-hidden"
      } `}
    >
      <div id="fides-banner">
        <div id="fides-banner-inner">
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
                onClick={handleManagePreferencesClick}
              />
            </span>
            <span className="fides-banner-buttons-right">
              <Button
                buttonType={ButtonType.PRIMARY}
                label={rejectButtonLabel}
                onClick={() => {
                  onRejectAll();
                  setBannerIsOpen(false);
                }}
              />
              <Button
                buttonType={ButtonType.PRIMARY}
                label={acceptButtonLabel}
                onClick={() => {
                  onAcceptAll();
                  setBannerIsOpen(false);
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
