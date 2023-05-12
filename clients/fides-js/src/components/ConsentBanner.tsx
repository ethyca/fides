import { h, FunctionComponent } from "preact";
import { useState, useEffect } from "preact/hooks";
import { ButtonType } from "../lib/consent-types";
import ConsentBannerButton from "./ConsentBannerButton";
import "../lib/banner.module.css";
import { useHasMounted } from "../lib/hooks";

interface BannerProps {
  bannerTitle?: string;
  bannerDescription?: string;
  confirmationButtonLabel?: string;
  rejectButtonLabel?: string;
  privacyCenterUrl: string;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  waitBeforeShow: number;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  bannerTitle = "Manage your consent",
  bannerDescription = "This website processes your data respectfully, so we require your consent to use cookies.",
  confirmationButtonLabel = "Accept All",
  rejectButtonLabel = "Reject All",
  privacyCenterUrl,
  onAcceptAll,
  onRejectAll,
  waitBeforeShow,
}) => {
  const [isShown, setIsShown] = useState(false);
  const hasMounted = useHasMounted();

  useEffect(() => {
    const delayBanner = setTimeout(() => {
      setIsShown(true);
    }, waitBeforeShow);
    return () => clearTimeout(delayBanner);
  }, [setIsShown, waitBeforeShow]);

  const navigateToPrivacyCenter = (): void => {
    if (privacyCenterUrl) {
      window.location.assign(privacyCenterUrl);
    }
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
        <ConsentBannerButton
          buttonType={ButtonType.TERTIARY}
          label="Manage Preferences"
          onClick={navigateToPrivacyCenter}
        />
        <ConsentBannerButton
          buttonType={ButtonType.SECONDARY}
          label={rejectButtonLabel}
          onClick={() => {
            onRejectAll();
            setIsShown(false);
          }}
        />
        <ConsentBannerButton
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
