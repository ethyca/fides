import { blueconic } from "../integrations/blueconic";
import { gtm } from "../integrations/gtm";
import { meta } from "../integrations/meta";
import { shopify } from "../integrations/shopify";
import {
  FidesCookie,
  FidesGlobal,
  FidesOptions,
  NoticeConsent,
  PrivacyExperience,
  UpdateConsentValidation,
} from "./consent-types";
import {
  decodeNoticeConsentString,
  defaultShowModal,
  encodeNoticeConsentString,
  shouldResurfaceBanner,
} from "./consent-utils";
import {
  consentCookieObjHasSomeConsentSet,
  updateExperienceFromCookieConsentNotices,
} from "./cookie";
import { onFidesEvent } from "./events";
import { DEFAULT_LOCALE, DEFAULT_MODAL_LINK_LABEL } from "./i18n";
import { updateConsent } from "./preferences";

declare global {
  interface Window {
    Fides: FidesGlobal;
    fides_overrides: Partial<FidesOptions>;
    fidesDebugger: (...args: unknown[]) => void;
  }
}

export const raise = (message: string) => {
  throw new Error(message);
};

export const updateWindowFides = (fidesGlobal: FidesGlobal) => {
  if (typeof window !== "undefined") {
    window.Fides = fidesGlobal;
  }
};

interface UpdateConsentApiOptions {
  consent?: NoticeConsent;
  fidesString?: string;
  validation?: UpdateConsentValidation;
}

/**
 * Since this method is called from the FidesGlobal object, we need to
 * validate the options, especially since the end user won't have the
 * benefit of the type system.
 */
const updateConsentApi = (
  fides: FidesGlobal,
  options: UpdateConsentApiOptions,
) => {
  // If neither consent nor fidesString is provided, raise an error
  if (!options?.consent && !options?.fidesString) {
    throw new Error("Either consent or fidesString must be provided");
  }

  // If `validation` is provided, validate it
  if (
    options.validation &&
    !Object.values(UpdateConsentValidation).includes(options.validation)
  ) {
    throw new Error(
      `Validation must be one of: ${Object.values(UpdateConsentValidation).join(
        ", ",
      )} (default is ${UpdateConsentValidation.THROW})`,
    );
  }
  return updateConsent(fides, options);
};

export interface UpdateExperienceProps {
  cookie: FidesCookie;
  experience: PrivacyExperience;
}
export const updateExperience = ({
  cookie,
  experience,
}: UpdateExperienceProps): Partial<PrivacyExperience> => {
  let updatedExperience: PrivacyExperience = experience;
  const preferencesExistOnCookie = consentCookieObjHasSomeConsentSet(
    cookie.consent,
  );
  if (preferencesExistOnCookie) {
    // If we have some preferences on the cookie, we update client-side experience with those preferences
    // if the name matches. This is used for client-side UI.
    updatedExperience = updateExperienceFromCookieConsentNotices({
      experience,
      cookie,
    });
  }
  return updatedExperience;
};

export const getCoreFides = ({
  tcfEnabled = false,
}: {
  tcfEnabled?: boolean;
}): Omit<FidesGlobal, "init"> => {
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
    reinitialize(this: FidesGlobal): Promise<void> {
      if (typeof this.init !== "function") {
        return Promise.reject(new Error("Fides.init method is not available"));
      }
      if (!this.config || !this.initialized) {
        raise("Fides must be initialized before reinitializing");
      }
      return this.init();
    },
    shouldShowExperience(this: FidesGlobal): boolean {
      if (
        !this?.experience ||
        !this?.cookie ||
        !this?.saved_consent ||
        !this?.options
      ) {
        // Can't show experience if required data is missing
        return false;
      }
      return shouldResurfaceBanner(
        this.experience,
        this.cookie,
        this.saved_consent,
        this.options,
      );
    },
    updateConsent(
      this: FidesGlobal,
      options: UpdateConsentApiOptions,
    ): Promise<void> {
      return updateConsentApi(this, options);
    },
  };
};
