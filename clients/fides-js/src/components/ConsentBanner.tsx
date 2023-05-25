import { h, FunctionComponent } from "preact";
import { useState, useEffect } from "preact/hooks";
import { ButtonType, ExperienceConfig } from "../lib/consent-types";
import Button from "./Button";
import "../lib/overlay.module.css";
import { useHasMounted } from "../lib/hooks";

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
  managePreferencesLabel = "Manage preferences",
  onOpenModal,
}) => {
  const [isShown, setIsShown] = useState(false);
  const hasMounted = useHasMounted();
  const {
    banner_title: bannerTitle = "Manage your consent",
    banner_description:
      bannerDescription = "This website processes your data respectfully, so we require your consent to use cookies.",
    confirmation_button_label: confirmationButtonLabel = "Accept All",
    reject_button_label: rejectButtonLabel = "Reject All",
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

  if (!hasMounted) {
    return null;
  }

  return (
    <div
      id="fides-consent-banner"
      className={`fides-consent-banner fides-consent-banner-bottom ${
        isShown ? "" : "fides-consent-banner-hidden"
      } `}
    >
      <div>
        <div
          id="fides-consent-banner-title"
          className="fides-consent-banner-title"
        >
          {bannerTitle || ""}
        </div>
        <div
          id="fides-consent-banner-description"
          className="fides-consent-banner-description"
        >
          {bannerDescription || ""}
        </div>
      </div>
      <div
        id="fides-consent-banner-buttons"
        className="fides-consent-banner-buttons"
      >
        <Button
          buttonType={ButtonType.SECONDARY}
          label={managePreferencesLabel}
          onClick={handleManagePreferencesClick}
        />
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
          label={confirmationButtonLabel}
          onClick={() => {
            onAcceptAll();
            setIsShown(false);
          }}
        />
      </div>
    </div>
  );
};

export default ConsentBanner;
