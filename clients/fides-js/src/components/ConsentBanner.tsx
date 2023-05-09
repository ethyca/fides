import { h, FunctionComponent } from "preact";
import { useState, useEffect } from "preact/hooks";
import { ButtonType, ConsentBannerOptions } from "../lib/consent-types";
import { debugLog } from "../lib/consent-utils";
import ConsentBannerButton from "./ConsentBannerButton";
import "../lib/banner.module.css";

interface BannerProps {
  options: ConsentBannerOptions;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  waitBeforeShow: number;
}

const ConsentBanner: FunctionComponent<BannerProps> = ({
  options,
  onAcceptAll,
  onRejectAll,
  waitBeforeShow,
}) => {
  const [isShown, setIsShown] = useState(false);
  useEffect(() => {
    const delayBanner = setTimeout(() => {
      setIsShown(true);
    }, waitBeforeShow);
    return () => clearTimeout(delayBanner);
  }, [setIsShown, waitBeforeShow]);
  const navigateToPrivacyCenter = (): void => {
    debugLog("Navigate to Privacy Center URL:", options.privacyCenterUrl);
    if (options.privacyCenterUrl) {
      window.location.assign(options.privacyCenterUrl);
    }
  };
  // TODO: support option to specify top/bottom
  return (
    <div
      id="fides-consent-banner"
      className={`fides-consent-banner fides-consent-banner-bottom ${
        isShown ? "" : "fides-consent-banner-hidden"
      } `}
    >
      <div
        id="fides-consent-banner-description"
        className="fides-consent-banner-description"
      >
        {options.labels?.bannerDescription || ""}
      </div>
      <div
        id="fides-consent-banner-buttons"
        className="fides-consent-banner-buttons"
      >
        <ConsentBannerButton
          buttonType={ButtonType.TERTIARY}
          label={options.labels?.tertiaryButton}
          onClick={navigateToPrivacyCenter}
        />
        <ConsentBannerButton
          buttonType={ButtonType.SECONDARY}
          label={options.labels?.secondaryButton}
          onClick={() => {
            onRejectAll();
            setIsShown(false);
            // TODO: save to Fides consent request API
            // eslint-disable-next-line no-console
            console.error(
              "Could not save consent record to Fides API, not implemented!"
            );
          }}
        />
        <ConsentBannerButton
          buttonType={ButtonType.PRIMARY}
          label={options.labels?.primaryButton}
          onClick={() => {
            onAcceptAll();
            setIsShown(false);
            // TODO: save to Fides consent request API
            // eslint-disable-next-line no-console
            console.error(
              "Could not save consent record to Fides API, not implemented!"
            );
          }}
        />
      </div>
    </div>
  );
};

export default ConsentBanner;
