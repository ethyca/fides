import { blueconic } from "../integrations/blueconic";
import { gtm } from "../integrations/gtm";
import { meta } from "../integrations/meta";
import { shopify } from "../integrations/shopify";
import { FidesGlobal } from "./consent-types";
import {
  decodeNoticeConsentString,
  defaultShowModal,
  encodeNoticeConsentString,
} from "./consent-utils";
import { onFidesEvent } from "./events";
import { DEFAULT_LOCALE, DEFAULT_MODAL_LINK_LABEL } from "./i18n";

export const getCoreFides = ({
  tcfEnabled = false,
}: {
  tcfEnabled?: boolean;
}): Omit<FidesGlobal, "init" | "reinitialize" | "shouldShowExperience"> => {
  return {
    consent: {},
    experience: undefined,
    geolocation: {},
    locale: DEFAULT_LOCALE,
    options: {
      debug: true,
      isOverlayEnabled: false,
      isPrefetchEnabled: false,
      isGeolocationEnabled: false,
      geolocationApiUrl: "",
      overlayParentId: null,
      modalLinkId: null,
      privacyCenterUrl: "",
      fidesApiUrl: "",
      tcfEnabled,
      gppEnabled: false,
      fidesEmbed: false,
      fidesDisableSaveApi: false,
      fidesDisableNoticesServedApi: false,
      fidesDisableBanner: false,
      fidesString: null,
      apiOptions: null,
      fidesTcfGdprApplies: tcfEnabled,
      fidesJsBaseUrl: "",
      customOptionsPath: null,
      preventDismissal: false,
      allowHTMLDescription: null,
      base64Cookie: false,
      fidesPrimaryColor: null,
      fidesClearCookie: false,
      showFidesBrandLink: !tcfEnabled,
      fidesConsentOverride: null,
      otFidesMapping: null,
      fidesDisabledNotices: null,
      fidesConsentNonApplicableFlagMode: null,
      fidesConsentFlagType: null,
    },
    fides_meta: {},
    identity: {},
    tcf_consent: {},
    saved_consent: {},
    config: undefined,
    initialized: false,
    onFidesEvent,
    blueconic,
    gtm,
    meta,
    shopify,
    showModal: defaultShowModal,
    getModalLinkLabel: () => DEFAULT_MODAL_LINK_LABEL,
    encodeNoticeConsentString,
    decodeNoticeConsentString,
  };
};
