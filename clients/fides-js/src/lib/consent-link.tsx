import { h, Component, VNode } from "preact";
import { CookieKeyConsent, hasSavedConsentCookie } from "./cookie";
import debugLog, { getBannerOptions } from "./consent-utils";
import { ConsentBannerOptions } from "./consent-types";

interface LinkProps {
  defaults: CookieKeyConsent;
  options: ConsentBannerOptions;
}

class ConsentLink extends Component<LinkProps> {
  private readonly options: ConsentBannerOptions;

  constructor(props: LinkProps) {
    super(props);
    this.options = props.options;
  }

  /**
   * Builds the DOM elements for the consent banner (container, buttons, etc.) and
   * return a single div that can be added to the body.
   */
  buildLink = () => {
    const options: ConsentBannerOptions = getBannerOptions();
    // todo- implement opening modal depending on privacy experience
    return <a href={options.privacyCenterUrl}>{options.consentLinkText}</a>;
  };

  render(): VNode | null {
    let linkBuild = null;
    // If the user provides any extra options, override the defaults
    try {
      if (hasSavedConsentCookie()) {
        // todo- check for device id too
        // also does the existence of a device id prevent links from rendering too, or just banners?
        debugLog(
          "Fides consent cookie already exists, skipping banner initialization!"
        );
        return null;
      }
      debugLog(
        "Fides consent link should be shown! Building banner elements & styles..."
      );
      linkBuild = this.buildLink();
    } catch (e) {
      debugLog(e);
    }
    return linkBuild;
  }
}

export default ConsentLink;
