import {h, Component, VNode} from "preact";
import {useState, useEffect} from "preact/hooks";
import {CookieKeyConsent, setConsentCookieAcceptAll, setConsentCookieRejectAll} from "./cookie";
import {ButtonType, ConsentBannerOptions} from "./consent-types";
import debugLog from "./consent-utils";
import ConsentBannerButton from "./ConsentBannerButton";

interface BannerProps {
  defaults: CookieKeyConsent;
  options: ConsentBannerOptions;
  waitBeforeShow: number;
}

interface BannerState {
  isShown: boolean;
}

class ConsentBanner extends Component<BannerProps, BannerState> {


  private readonly defaults: CookieKeyConsent;

  private readonly options: ConsentBannerOptions;

  private readonly waitBeforeShow: number;

  constructor(props: BannerProps) {
    super(props);
    this.defaults = props.defaults;
    this.options = props.options;
    this.waitBeforeShow = props.waitBeforeShow;
  }

  /**
   * Navigates to the Fides Privacy Center to manage consent settings
   */
  navigateToPrivacyCenter = (): void => {
    debugLog("Navigate to Privacy Center URL:", this.options.privacyCenterUrl);
    if (this.options.privacyCenterUrl) {
      window.location.assign(this.options.privacyCenterUrl);
    }
  };

  /**
   * Builds the DOM elements for the consent banner (container, buttons, etc.) and
   * return a single div that can be added to the body.
   */
  buildBanner = (defaults: CookieKeyConsent) => {
    const [isShown, setIsShown] = useState(false)

    useEffect(() => {
      const delayBanner = setTimeout(() => {
        setIsShown(true)
      }, this.waitBeforeShow)
      return () => clearTimeout(delayBanner)
    }, [setIsShown, this.waitBeforeShow])
    // TODO: support option to specify top/bottom
    return (
      <div
        id="fides-consent-banner"
        class={`fides-consent-banner fides-consent-banner-bottom ${
          isShown ? "" : "fides-consent-banner-hidden" 
        } `}
      >
        <div
          id="fides-consent-banner-description"
          class="fides-consent-banner-description"
        >
          {this.options.labels?.bannerDescription || ""}
        </div>
        <div
          id="fides-consent-banner-buttons"
          class="fides-consent-banner-buttons"
        >
          <ConsentBannerButton
            buttonType={ButtonType.TERTIARY}
            label={this.options.labels?.tertiaryButton}
            onClick={this.navigateToPrivacyCenter}>
          </ConsentBannerButton>
          <ConsentBannerButton
            buttonType={ButtonType.SECONDARY}
            label={this.options.labels?.secondaryButton}
            onClick={() => {
            setConsentCookieRejectAll(defaults);
            setIsShown(false);
            // TODO: save to Fides consent request API
            // eslint-disable-next-line no-console
            console.error(
                "Could not save consent record to Fides API, not implemented!"
            );
          }}>
          </ConsentBannerButton>
          <ConsentBannerButton
            buttonType={ButtonType.PRIMARY}
            label={this.options.labels?.primaryButton}
            onClick={() => {
            setConsentCookieAcceptAll(defaults);
            setIsShown(false);
            // TODO: save to Fides consent request API
            // eslint-disable-next-line no-console
            console.error(
                "Could not save consent record to Fides API, not implemented!"
            );
          }}>
          </ConsentBannerButton>
        </div>
      </div>
    );
  };

  render(): VNode | null {
    let bannerBuild = null;
    try {
      debugLog(
        "Fides consent banner should be shown! Building banner elements & styles..."
      );
      bannerBuild = this.buildBanner(this.defaults);
    } catch (e) {
      debugLog(e);
    }
    return bannerBuild;
  }
}

export default ConsentBanner;
