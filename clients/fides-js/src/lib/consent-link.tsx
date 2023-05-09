import { h, Component, VNode } from "preact";
import debugLog from "./consent-utils";
import { ConsentBannerOptions } from "./consent-types";

interface LinkProps {
  options: ConsentBannerOptions;
}

class ConsentLink extends Component<LinkProps> {
  /**
   * Builds the DOM elements for the consent banner (container, buttons, etc.) and
   * return a single div that can be added to the body.
   */
  static buildLink = (options: ConsentBannerOptions) =>
    // todo- implement opening modal depending on privacy experience
     <a href={options.privacyCenterUrl}>{options.consentLinkText}</a>
  ;

  private readonly options: ConsentBannerOptions;

  constructor(props: LinkProps) {
    super(props);
    this.options = props.options;
  }

  render(): VNode | null {
    let linkBuild = null;
    // If the user provides any extra options, override the defaults
    try {
      debugLog(
        "Fides consent link should be shown! Building banner elements & styles..."
      );
      linkBuild = ConsentLink.buildLink(this.options);
    } catch (e) {
      debugLog(e);
    }
    return linkBuild;
  }
}

export default ConsentLink;
