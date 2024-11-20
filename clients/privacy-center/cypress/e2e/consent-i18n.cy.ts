/* eslint-disable spaced-comment */
import {
  ExperienceConfigTranslation,
  FidesEndpointPaths,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyNotice,
} from "fides-js";

import { Locale } from "~/../fides-js/src/lib/i18n";

import { API_URL, TEST_OVERRIDE_WINDOW_PATH } from "../support/constants";
import { stubConfig, stubTCFExperience } from "../support/stubs";

/**
 * Define (lots of) reusable test data for all the tests!
 */
type TestFixture =
  | "experience_banner_modal.json"
  | "experience_banner_modal_notice_only.json"
  | "experience_tcf.json"
  | "experience_tcf_minimal.json"
  | "experience_privacy_center.json";

type TestBannerTranslations = {
  banner_title: string;
  banner_description: string;
  privacy_preferences_link_label: string;
  reject_button_label: string;
  accept_button_label: string;
  acknowledge_button_label: string;
  gpc_label: string;
  gpc_status_label: string;
  privacy_policy_link_label: string | null;
  privacy_policy_url: string | null;
};

type TestModalTranslations = {
  title: string;
  description: string;
  save_button_label: string;
  reject_button_label: string;
  accept_button_label: string;
  acknowledge_button_label: string;
  gpc_title: string;
  gpc_description: string;
  gpc_label: string;
  gpc_applied_label: string;
  gpc_overridden_label: string;
  privacy_policy_link_label: string | null;
  privacy_policy_url: string | null;
};

type TestNoticeTranslations = {
  title: string;
  description: string;
};

type TestTcfBannerTranslations = TestBannerTranslations & {
  purpose_header: string;
  purpose_example: string;
};

type TestTcfModalTranslations = TestModalTranslations & {
  purposes: string;
  purposes_description: string;
  purpose_example: string;
  purpose_example_description: string;
  purpose_example_illustration: string;
  special_purposes: string;
  special_purpose_example: string;
  special_purpose_example_description: string;
  special_purpose_example_illustration: string;
  features: string;
  features_description: string;
  feature_example: string;
  feature_example_description: string;
  special_features: string;
  special_feature_example: string;
  special_feature_example_description: string;
  vendors: string;
  vendors_description: string;
  vendors_iab: string;
  vendor_iab_example: string;
  vendor_iab_example_description: string;
  vendors_other: string;
  vendor_other_example: string;
  vendor_other_example_description: string;
  vendor_privacy_policy: string;
  vendor_legint_disclosure: string;
  retention: string;
  consent: string;
  legint: string;
  data_categories: string;
};

/**********************************************************
 *
 * EXPECTED TRANSLATION STRINGS
 *
 * NOTE: There is a *lot* of duplication here between test data, fixture data,
 * and the static translations in fides.js project. We *could* automatically
 * import those strings here... but it's much easier to *read* these tests when
 * the expected strings are all here. This also helps us catch any accidental
 * changes to strings or misspellings!
 *
 **********************************************************/

/**
 * English translations for banner & modal
 */
const ENGLISH_BANNER: TestBannerTranslations = {
  banner_title: "[banner] Manage your consent preferences",
  banner_description: "[banner] We use cookies and similar",
  privacy_preferences_link_label: "Manage preferences",
  reject_button_label: "Opt out of all",
  accept_button_label: "Opt in to all",
  acknowledge_button_label: "OK",
  gpc_label: "Global Privacy Control",
  gpc_status_label: "Applied",
  privacy_policy_link_label: "Privacy Policy",
  privacy_policy_url: "https://privacy.example.com/",
};

const ENGLISH_MODAL: TestModalTranslations = {
  title: "Manage your consent preferences",
  description: "We use cookies and similar",
  save_button_label: "Save",
  reject_button_label: "Opt out of all",
  accept_button_label: "Opt in to all",
  acknowledge_button_label: "OK",
  gpc_title: "Global Privacy Control detected",
  gpc_description: "Your global privacy control preference has been honored.",
  gpc_label: "Global Privacy Control",
  gpc_applied_label: "Applied",
  gpc_overridden_label: "Overridden",
  privacy_policy_link_label: "Privacy Policy",
  privacy_policy_url: "https://privacy.example.com/",
};

const ENGLISH_NOTICES: TestNoticeTranslations[] = [
  { title: "Advertising", description: "This website uses marketing" },
  { title: "Analytics", description: "This website uses analytics" },
  { title: "Essential", description: "This website uses essential" },
];

/**
 * English translations for TCF banner & modal
 */
const ENGLISH_TCF_BANNER: TestTcfBannerTranslations = {
  ...ENGLISH_BANNER,
  ...{
    banner_description:
      "[banner] We, and our 16 vendors, use cookies and similar",
    purpose_header: "We use data for the following purposes",
    purpose_example: "Use limited data to select",
  },
};

const ENGLISH_TCF_MODAL: TestTcfModalTranslations = {
  ...ENGLISH_MODAL,
  ...{
    description: "We, and our 16 vendors, use cookies and similar",
    purposes: "Purposes",
    purposes_description: "Below, you will find a list of the purposes",
    purpose_example: "Use profiles to select personalised advertising",
    purpose_example_description: "Advertising presented to you on this service",
    purpose_example_illustration: "An online retailer wants to advertise",
    special_purposes: "Special purposes",
    special_purpose_example: "Ensure security",
    special_purpose_example_description: "Your data can be used to monitor",
    special_purpose_example_illustration:
      "An advertising intermediary delivers ads",
    features: "Features",
    features_description: "Below, you will find a list of the features",
    feature_example: "Match and combine data",
    feature_example_description: "Information about your activity",
    special_features: "Special features",
    special_feature_example: "Use precise geolocation data",
    special_feature_example_description:
      "With your acceptance, your precise location",
    vendors: "Vendors",
    vendors_description: "Below, you will find a list of vendors",
    vendors_iab: "IAB TCF Vendors",
    vendor_iab_example: "Captify",
    vendor_iab_example_description:
      "Captify stores cookies with a maximum duration",
    vendors_other: "Other vendors",
    vendor_other_example: "Fides System",
    vendor_other_example_description:
      "Fides System stores cookies with a maximum duration",
    vendor_privacy_policy: "Privacy policy",
    vendor_legint_disclosure: "Legitimate interest disclosure",
    retention: "Retention",
    consent: "Consent",
    legint: "Legitimate interest",
    data_categories: "Data categories",
  },
};

/**
 * Spanish translations for banner & modal
 */
const SPANISH_BANNER: TestBannerTranslations = {
  banner_title: "[banner] Administrar sus preferencias de consentimiento",
  banner_description: "[banner] Usamos cookies y métodos similares",
  privacy_preferences_link_label: "Administrar preferencias",
  reject_button_label: "No participar en nada",
  accept_button_label: "Participar en todo",
  acknowledge_button_label: "Aceptar",
  gpc_label: "Control de privacidad global",
  gpc_status_label: "Aplicado",
  privacy_policy_link_label: "Política de privacidad",
  privacy_policy_url: "https://privacy.example.com/",
};

const SPANISH_MODAL: TestModalTranslations = {
  title: "Administrar sus preferencias de consentimiento",
  description: "Usamos cookies y métodos similares",
  save_button_label: "Guardar",
  reject_button_label: "No participar en nada",
  accept_button_label: "Participar en todo",
  acknowledge_button_label: "Aceptar",
  gpc_title: "Control de privacidad global detectado",
  gpc_description:
    "Su preferencia de control de privacidad global se ha respetado.",
  gpc_label: "Control de privacidad global",
  gpc_applied_label: "Aplicado",
  gpc_overridden_label: "Anulado",
  privacy_policy_link_label: "Política de privacidad",
  privacy_policy_url: "https://privacy.example.com/",
};

const SPANISH_NOTICES: TestNoticeTranslations[] = [
  {
    title: "Mercadotecnia",
    description: "Este sitio web usa cookies y servicios de mercadotecnia",
  },
  {
    title: "Análisis",
    description: "Este sitio web usa cookies analíticas y servicios",
  },
  {
    title: "Esenciales",
    description: "Este sitio web utiliza cookies esenciales y servicios",
  },
];

/**
 * Spanish translations for TCF banner & modal
 */
const SPANISH_TCF_BANNER: TestTcfBannerTranslations = {
  ...SPANISH_BANNER,
  ...{
    banner_description: "[banner] Nosotros, y nuestros 16 vendadores, usamos",
    purpose_header: "Usamos datos para los siguientes propósitos",
    purpose_example: "Uso de datos limitados para seleccionar anuncios básicos",
  },
};

const SPANISH_TCF_MODAL: TestTcfModalTranslations = {
  ...SPANISH_MODAL,
  ...{
    description: "Nosotros, y nuestros 16 vendadores, usamos",
    purposes: "Propósitos",
    purposes_description:
      "A continuación encontrará una lista de los propósitos",
    purpose_example:
      "Utilizar perfiles para seleccionar la publicidad personalizada",
    purpose_example_description: "La publicidad presentada en este servicio",
    purpose_example_illustration: "Un minorista que opera en Internet",
    special_purposes: "Propósitos especiales",
    special_purpose_example: "Garantizar la seguridad",
    special_purpose_example_description:
      "Tus datos pueden utilizarse para supervisar",
    special_purpose_example_illustration:
      "Un intermediario publicitario entrega anuncios",
    features: "Características",
    features_description:
      "A continuación encontrará una lista de las características",
    feature_example:
      "Cotejo y combinación de datos procedentes de otras fuentes de información",
    feature_example_description: "La información en relación con tu actividad",
    special_features: "Características especiales",
    special_feature_example:
      "Utilizar datos de localización geográfica precisa",
    special_feature_example_description:
      "Al contar con tu aprobación, tu ubicación exacta",
    vendors: "Proveedores",
    vendors_description:
      "A continuación encontrará una lista de los proveedores",
    vendors_iab: "Proveedores IAB TCF",
    vendor_iab_example: "Captify",
    vendor_iab_example_description: "Captify almacena cookies con una duración",
    vendors_other: "Otros proveedores",
    vendor_other_example: "Fides System",
    vendor_other_example_description:
      "Fides System almacena cookies con una duración",
    vendor_privacy_policy: "Política de privacidad",
    vendor_legint_disclosure: "Revelación de interés legítimo",
    retention: "Conservación",
    consent: "Consentimiento",
    legint: "Interés legítimo",
    data_categories: "Categorías de datos",
  },
};

/**********************************************************
 *
 *  🇺🇸🇪🇸🇯🇵 CONSENT INTERNATIONALIZATION (I18N) TESTS 🇺🇸🇪🇸🇯🇵
 *
 **********************************************************/
const ENGLISH_LOCALE = "en";
const SPANISH_LOCALE = "es";
const FRENCH_LOCALE = "fr-CA";
const JAPANESE_LOCALE = "ja-JP";

describe("Consent i18n", () => {
  /**
   * Visit the fides-js-components-demo page using:
   * @param navigatorLanguage language to set in the browser for localization
   * @param fixture PrivacyExperience fixture to load (e.g. "experience_banner_modal.json")
   * @param globalPrivacyControl value to set in the browser for GPC
   * @param options FidesJS options to inject
   * @param queryParams query params to set in the browser (e.g. "?fides_locale=es")
   * @param overrideExperience callback function to override the PrivacyExperience fixture before loading
   */
  const visitDemoWithI18n = (props: {
    navigatorLanguage: string;
    fixture?: TestFixture;
    globalPrivacyControl?: boolean;
    options?: Partial<FidesInitOptions>;
    queryParams?: Cypress.VisitOptions["qs"];
    overrideExperience?: (experience: PrivacyExperience) => PrivacyExperience;
  }) => {
    cy.on("window:before:load", (win) => {
      Object.defineProperty(win.navigator, "language", {
        value: props.navigatorLanguage,
      });
      if (typeof props.globalPrivacyControl !== "undefined") {
        Object.defineProperty(win.navigator, "globalPrivacyControl", {
          value: props.globalPrivacyControl,
        });
      }
    });
    if (props?.options?.tcfEnabled) {
      stubTCFExperience({
        stubOptions: { ...props.options, fidesLocale: props.navigatorLanguage },
        demoPageQueryParams: props.queryParams,
      });
    } else {
      cy.fixture(`consent/${props.fixture}`).then((data) => {
        let experience = data.items[0];
        cy.log(
          "Using overridden PrivacyExperience data from overrideExperience()",
          experience,
        );
        if (props.overrideExperience) {
          experience = props.overrideExperience(experience);
          cy.log(
            "Using overridden PrivacyExperience data from overrideExperience()",
            experience,
          );
        }
        stubConfig(
          { experience, options: props.options },
          null,
          null,
          props.queryParams,
        );
      });
    }
    cy.window().its("navigator.language").should("eq", props.navigatorLanguage);
  };

  /**********************************************************
   *
   * FIDESJS BANNER + MODAL TESTS
   *
   **********************************************************/
  describe("when localizing banner_and_modal components", () => {
    const testBannerLanguageMenu = (locale: Locale) => {
      cy.get("#fides-banner").within(() => {
        cy.getByTestId(`fides-i18n-option-${locale}`).should(
          "have.attr",
          "aria-pressed",
        );
      });
    };
    // Reusable assertions to test that the banner component localizes correctly
    const testBannerLocalization = (t: TestBannerTranslations) => {
      /**
       * Check banner localization
       *
       * NOTE: These checks will not pass on a "notice-only" banner variant, since
       * many of the buttons are not seen there. See the dedicated notice-only
       * specs for those tests instead!
       */
      cy.get("#fides-banner").within(() => {
        cy.get(".fides-banner-title").contains(t.banner_title);
        cy.get(".fides-banner-description").contains(t.banner_description);
        cy.get("#fides-button-group").contains(
          t.privacy_preferences_link_label,
        );
        cy.get("#fides-button-group").contains(t.reject_button_label);
        cy.get("#fides-button-group").contains(t.accept_button_label);
        cy.get(".fides-gpc-label").contains(t.gpc_label);
        cy.get(".fides-gpc-label .fides-gpc-badge").contains(
          t.gpc_status_label,
        );

        // Privacy policy link is optional; if provided, check that it is localized
        if (t.privacy_policy_link_label && t.privacy_policy_url) {
          cy.get("#fides-privacy-policy-link").contains(
            t.privacy_policy_link_label,
          );
          cy.get("#fides-privacy-policy-link a").should(
            "have.attr",
            "href",
            t.privacy_policy_url,
          );
        } else {
          cy.get("#fides-privacy-policy-link").should("not.exist");
        }
      });
    };

    // Reusable assertions to test that the modal component localizes correctly
    const openAndTestModalLocalization = (t: TestModalTranslations) => {
      // Start by opening the modal
      // NOTE: We could also use cy.get("#fides-modal-link").click(), but let's
      // assume the banner is visible in these tests
      cy.get("#fides-banner .fides-manage-preferences-button").click();
      cy.get("#fides-modal").should("be.visible");

      // Check modal localization
      cy.get("#fides-modal").within(() => {
        cy.get(".fides-modal-title").contains(t.title);
        cy.get(".fides-modal-description").contains(t.description);
        cy.get(".fides-modal-button-group").contains(t.save_button_label);
        cy.get(".fides-modal-button-group").contains(t.reject_button_label);
        cy.get(".fides-modal-button-group").contains(t.accept_button_label);
        cy.get(".fides-gpc-banner .fides-gpc-header").contains(t.gpc_title);
        cy.get(".fides-gpc-banner").contains(t.gpc_title);

        // Privacy policy link is optional; if provided, check that it is localized
        if (t.privacy_policy_link_label && t.privacy_policy_url) {
          cy.get("#fides-privacy-policy-link").contains(
            t.privacy_policy_link_label,
          );
          cy.get("#fides-privacy-policy-link a").should(
            "have.attr",
            "href",
            t.privacy_policy_url,
          );
        } else {
          cy.get("#fides-privacy-policy-link").should("not.exist");
        }
      });
    };

    // Reusable assertions to test that the modal notices component localizes correctly
    const testModalNoticesLocalization = (t: TestNoticeTranslations[]) => {
      // Check modal notices localization
      cy.get("#fides-modal .fides-modal-notices").within(() => {
        t.forEach((notice) => {
          cy.get(".fides-notice-toggle-title").contains(notice.title).click();
          cy.get(".fides-disclosure-visible").contains(notice.description);
          cy.get(".fides-notice-toggle-title").contains(notice.title).click();
        });
      });
    };

    /**
     * Define our parameterized test cases to generate specs below!
     */
    const fixture = "experience_banner_modal.json";
    const tests = [
      {
        navigatorLanguage: ENGLISH_LOCALE,
        locale: ENGLISH_LOCALE,
        banner: ENGLISH_BANNER,
        modal: ENGLISH_MODAL,
        notices: ENGLISH_NOTICES,
      },
      {
        navigatorLanguage: SPANISH_LOCALE,
        locale: SPANISH_LOCALE,
        banner: SPANISH_BANNER,
        modal: SPANISH_MODAL,
        notices: SPANISH_NOTICES,
      },
    ];

    tests.forEach(({ navigatorLanguage, locale, banner, modal, notices }) => {
      describe(`when browser language matches available locale (${navigatorLanguage})`, () => {
        it(`localizes banner_and_modal components in the correct locale (${locale})`, () => {
          visitDemoWithI18n({
            navigatorLanguage,
            globalPrivacyControl: true,
            fixture,
          });
          testBannerLocalization(banner);
          openAndTestModalLocalization(modal);
          testModalNoticesLocalization(notices);
        });

        it("handles optional translations for banner_and_modal components", () => {
          // Ensure that null/empty values for some optional translation messages provide their correct fallbacks
          visitDemoWithI18n({
            navigatorLanguage,
            globalPrivacyControl: true,
            fixture,
            overrideExperience: (experience: any) => {
              /* eslint-disable no-param-reassign */
              const translations =
                experience.experience_config.translations.find(
                  (e: any) => e.language === locale,
                );
              translations.banner_description = null;
              translations.banner_title = "";
              translations.privacy_policy_link_label = null;
              translations.privacy_policy_url = null;
              return experience;
              /* eslint-enable no-param-reassign */
            },
          });

          testBannerLocalization({
            ...banner,
            ...{
              // Expect banner to fallback to modal translations
              banner_title: modal.title,
              banner_description: modal.description,
              // Expect privacy policy link to not exist
              privacy_policy_link_label: null,
              privacy_policy_url: null,
            },
          });
          openAndTestModalLocalization({
            ...modal,
            ...{
              // Expect privacy policy link to not exist
              privacy_policy_link_label: null,
              privacy_policy_url: null,
            },
          });
          testModalNoticesLocalization(notices);
        });

        it(`localizes banner_and_modal notice-only components in the correct locale (${locale})`, () => {
          visitDemoWithI18n({
            navigatorLanguage,
            globalPrivacyControl: true,
            fixture: "experience_banner_modal_notice_only.json",
          });

          // Test notice-only banner
          cy.get("#fides-banner").within(() => {
            cy.get(".fides-banner-title").contains(banner.banner_title);
            cy.get(".fides-banner-description").contains(
              banner.banner_description,
            );
            cy.get(".fides-acknowledge-button").contains(
              banner.acknowledge_button_label,
            );
          });

          // Test notice-only modal
          cy.get("#fides-modal-link").click();
          cy.get("#fides-modal").within(() => {
            cy.get(".fides-modal-title").contains(modal.title);
            cy.get(".fides-modal-description").contains(modal.description);
            cy.get(".fides-acknowledge-button").contains(
              modal.acknowledge_button_label,
            );
          });
        });

        it.skip(`localizes modal components in the correct locale (${locale})`, () => {});

        it(`localizes GPC badges on notices in the correct locale ($locale})`, () => {
          // Set GPC flag on the first notice
          visitDemoWithI18n({
            navigatorLanguage,
            globalPrivacyControl: true,
            fixture,
            overrideExperience: (experience: any) => {
              /* eslint-disable no-param-reassign */
              // Modify the first notice (Advertising) to set the GPC flag
              const testNotices: PrivacyNotice[] = experience.privacy_notices;
              const adsNotice = testNotices[0];
              cy.wrap(adsNotice).should(
                "have.property",
                "id",
                "pri_notice-advertising-000",
              );
              adsNotice.has_gpc_flag = true;
              return experience;
              /* eslint-enable no-param-reassign */
            },
          });

          // Open the modal and check the notices themselves are translated
          testBannerLocalization(banner);
          openAndTestModalLocalization(modal);
          testModalNoticesLocalization(notices);

          // Check the GPC badge labels on the first notice
          cy.get(
            "#fides-modal .fides-modal-notices .fides-notice-toggle:first",
          ).within(() => {
            cy.get(".fides-notice-toggle-title").contains(notices[0].title);
            cy.get(".fides-gpc-label").contains(modal.gpc_label);
            cy.get(".fides-gpc-label .fides-gpc-badge").contains(
              modal.gpc_applied_label,
            );
            cy.get(".fides-toggle-input").click();
            cy.get(".fides-gpc-label .fides-gpc-badge").contains(
              modal.gpc_overridden_label,
            );
          });
          cy.get(
            "#fides-modal .fides-modal-notices .fides-notice-toggle:last",
          ).within(() => {
            cy.get(".fides-gpc-label").should("not.exist");
          });
        });
      });
    });

    describe(`when browser language does not match any available locale (${JAPANESE_LOCALE})`, () => {
      it(`localizes banner_and_modal components in the default locale (${ENGLISH_LOCALE})`, () => {
        visitDemoWithI18n({
          navigatorLanguage: JAPANESE_LOCALE,
          globalPrivacyControl: true,
          fixture,
        });
        testBannerLocalization(ENGLISH_BANNER);
        openAndTestModalLocalization(ENGLISH_MODAL);
        testModalNoticesLocalization(ENGLISH_NOTICES);
      });
    });

    describe("when auto_detect_language is false", () => {
      it(`ignores browser locale (${SPANISH_LOCALE}) and localizes in the default locale (${ENGLISH_LOCALE})`, () => {
        // Visit the demo site in Spanish, but expect English translations when auto-detection is disabled
        visitDemoWithI18n({
          navigatorLanguage: SPANISH_LOCALE,
          globalPrivacyControl: true,
          fixture,
          overrideExperience: (experience) => {
            /* eslint-disable-next-line no-param-reassign */
            experience.experience_config!.auto_detect_language = false;
            return experience;
          },
        });
        testBannerLocalization(ENGLISH_BANNER);
        openAndTestModalLocalization(ENGLISH_MODAL);
        testModalNoticesLocalization(ENGLISH_NOTICES);
      });

      describe(`when an alternate default locale is specified in the experience (${SPANISH_LOCALE})`, () => {
        it(`ignores browser locale (${ENGLISH_LOCALE}) and localizes in the default locale from the experience (${SPANISH_LOCALE})`, () => {
          // Visit the demo site in English, but expect Spanish translations when auto-detection is disabled
          visitDemoWithI18n({
            navigatorLanguage: ENGLISH_LOCALE,
            globalPrivacyControl: true,
            fixture,
            overrideExperience: (experience) => {
              /* eslint-disable no-param-reassign */
              // Override the test data to specify Spanish as the default translation for the experience.
              experience.experience_config!.translations[0].is_default = false;
              experience.experience_config!.translations[1].is_default = true;
              // Disable auto-detection
              experience.experience_config!.auto_detect_language = false;
              return experience;
              /* eslint-enable no-param-reassign */
            },
          });
          testBannerLocalization(SPANISH_BANNER);
          openAndTestModalLocalization(SPANISH_MODAL);
          testModalNoticesLocalization(SPANISH_NOTICES);
        });
      });
    });

    describe(`when ?fides_locale override param is set to an available locale (${SPANISH_LOCALE})`, () => {
      it(`ignores browser locale and localizes in the override locale (${SPANISH_LOCALE})`, () => {
        // Visit the demo site in English, but expect Spanish translations when fides_locale override is set
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal.json",
          queryParams: { fides_locale: SPANISH_LOCALE },
        });
        testBannerLanguageMenu(SPANISH_LOCALE);
        testBannerLocalization(SPANISH_BANNER);
        openAndTestModalLocalization(SPANISH_MODAL);
        testModalNoticesLocalization(SPANISH_NOTICES);
      });
    });

    describe("when user selects their own locale", () => {
      it(`localizes in the user selected locale (${SPANISH_LOCALE})`, () => {
        // Visit the demo site in English, but expect Spanish translations when the user selects
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal.json",
        });
        cy.get("#fides-banner").should("be.visible");
        cy.get(
          `#fides-banner [data-testid='fides-i18n-option-${SPANISH_LOCALE}']`,
        ).focus();
        cy.get(`.fides-i18n-menu`).focused().click();
        testBannerLanguageMenu(SPANISH_LOCALE);
        testBannerLocalization(SPANISH_BANNER);
        openAndTestModalLocalization(SPANISH_MODAL);
        testModalNoticesLocalization(SPANISH_NOTICES);
      });
      it(`ignores query params and localizes in the user selected locale (${ENGLISH_LOCALE})`, () => {
        // Override the demo site in Spanish, but expect English translations when the user selects
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal.json",
          queryParams: { fides_locale: SPANISH_LOCALE },
        });
        cy.get("#fides-banner").should("be.visible");
        cy.get(
          `#fides-banner [data-testid='fides-i18n-option-${ENGLISH_LOCALE}']`,
        ).focus();
        cy.get(`.fides-i18n-menu`).focused().click();
        testBannerLanguageMenu(ENGLISH_LOCALE);
        testBannerLocalization(ENGLISH_BANNER);
        openAndTestModalLocalization(ENGLISH_MODAL);
        testModalNoticesLocalization(ENGLISH_NOTICES);
      });
    });

    /**
     * Special-case tests for mismatching translations between notices & experiences
     */
    describe(`when notices and experience have mismatched translations`, () => {
      describe(`when notices are missing translations that are available in the experience for the browser locale (${SPANISH_LOCALE})`, () => {
        beforeEach(() => {
          // Visit the demo in Spanish, but remove the Spanish translations from the Advertising notice
          visitDemoWithI18n({
            navigatorLanguage: SPANISH_LOCALE,
            globalPrivacyControl: true,
            fixture: "experience_banner_modal.json",
            overrideExperience: (experience: any) => {
              /* eslint-disable no-param-reassign */
              // Modify the first notice (Advertising) and remove the Spanish translations
              const testNotices: PrivacyNotice[] = experience.privacy_notices;
              const adsNotice = testNotices[0];
              cy.wrap(adsNotice).should(
                "have.property",
                "id",
                "pri_notice-advertising-000",
              );
              adsNotice.has_gpc_flag = true;
              adsNotice.translations = adsNotice.translations.filter(
                (e) => e.language !== SPANISH_LOCALE,
              );
              return experience;
              /* eslint-enable no-param-reassign */
            },
          });
        });

        it(`falls back to showing notices in the default locale (${ENGLISH_LOCALE}) and the experience in the correct locale (${SPANISH_LOCALE})`, () => {
          testBannerLocalization(SPANISH_BANNER);
          openAndTestModalLocalization(SPANISH_MODAL);
          testModalNoticesLocalization([
            ENGLISH_NOTICES[0], // fallback to English translation for first (Advertising) notice
            SPANISH_NOTICES[1],
            SPANISH_NOTICES[2],
          ]);
        });

        /* eslint-disable @typescript-eslint/naming-convention */
        it(`reports notices served and preferences saved using the correct privacy_notice_history_id for the default locale (${ENGLISH_LOCALE})`, () => {
          /**
           * Expect the notice history IDs used should be a mixture of English and Spanish notices:
           * 1) English advertising notice (fallback for missing Spanish translation)
           * 2) Spanish analytics notice (correct Spanish translation)
           * 3) Spanish essential notice (correct Spanish translation)
           */
          const EXPECTED_NOTICE_HISTORY_IDS = [
            "pri_notice-history-advertising-en-000", // English (en)
            "pri_notice-history-analytics-es-000", // Spanish (es)
            "pri_notice-history-essential-es-000", // Spanish (es)
          ];

          // First, expect GPC to auto-apply and save preferences to the API
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const {
              method,
              served_notice_history_id,
              privacy_experience_config_history_id,
              preferences,
            } = interception.request.body;
            expect(method).to.eq("gpc");
            expect(served_notice_history_id).to.be.a("string");
            expect(privacy_experience_config_history_id).to.eq(
              "pri_exp-history-banner-modal-es-000",
            );
            const noticeHistoryIDs = preferences.map(
              (e: any) => e.privacy_notice_history_id,
            );
            expect(noticeHistoryIDs).to.eql(EXPECTED_NOTICE_HISTORY_IDS);
          });

          // Open the modal and test the "notices served" API
          openAndTestModalLocalization(SPANISH_MODAL);
          cy.wait("@patchNoticesServed").then((interception) => {
            const {
              privacy_experience_config_history_id,
              privacy_notice_history_ids,
            } = interception.request.body;
            expect(privacy_experience_config_history_id).to.eq(
              "pri_exp-history-banner-modal-es-000",
            );
            expect(privacy_notice_history_ids).to.eql(
              EXPECTED_NOTICE_HISTORY_IDS,
            );
          });

          // Accept all notices and test the "privacy preferences" API
          cy.get("#fides-modal .fides-accept-all-button").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const {
              method,
              served_notice_history_id,
              privacy_experience_config_history_id,
              preferences,
            } = interception.request.body;
            expect(method).to.eq("accept");
            expect(served_notice_history_id).to.be.a("string");
            expect(privacy_experience_config_history_id).to.eq(
              "pri_exp-history-banner-modal-es-000",
            );
            const noticeHistoryIDs = preferences.map(
              (e: any) => e.privacy_notice_history_id,
            );
            expect(noticeHistoryIDs).to.eql(EXPECTED_NOTICE_HISTORY_IDS);
          });

          // TODO (PROD-1598): test that correct history ID used after user changes language
        });
        /* eslint-enable @typescript-eslint/naming-convention */
      });

      describe(`when an alternate default locale is specified in the experience (${SPANISH_LOCALE})`, () => {
        describe(`when the experience has translations matching the browser locale (${FRENCH_LOCALE}) but notices are missing translations`, () => {
          beforeEach(() => {
            // Visit the demo in French, but remove the French translations from the Advertising notice
            visitDemoWithI18n({
              navigatorLanguage: FRENCH_LOCALE,
              globalPrivacyControl: true,
              fixture: "experience_banner_modal.json",
              overrideExperience: (experience: any) => {
                /* eslint-disable no-param-reassign */
                // Override the test data to specify Spanish as the default translation for the experience.
                experience.experience_config!.translations[0].is_default =
                  false;
                experience.experience_config!.translations[1].is_default = true;
                // Modify the first notice (Advertising) and remove the French translations
                const testNotices: PrivacyNotice[] = experience.privacy_notices;
                const adsNotice = testNotices[0];
                cy.wrap(adsNotice).should(
                  "have.property",
                  "id",
                  "pri_notice-advertising-000",
                );
                adsNotice.has_gpc_flag = true;
                adsNotice.translations = adsNotice.translations.filter(
                  (e) => e.language !== FRENCH_LOCALE,
                );
                return experience;
                /* eslint-enable no-param-reassign */
              },
            });
          });

          it(`falls back to showing notices in the alternate default locale (${SPANISH_LOCALE}) and the experience in the correct locale (${FRENCH_LOCALE})`, () => {
            // Do some _lightweight_ checks for the French localization 🇫🇷
            cy.get("#fides-banner .fides-banner-title").contains(
              "[banner] Gestion de vos préférences de consentement",
            );
            cy.get("#fides-banner .fides-manage-preferences-button").click();
            cy.get("#fides-modal .fides-modal-title").contains(
              "Gestion de vos préférences de consentement",
            );

            // Test the notices are what we expect
            testModalNoticesLocalization([
              SPANISH_NOTICES[0], // fallback to Spani🇫🇷sh translation for first (Advertising) notice
              {
                title: "Analytique",
                description:
                  "Ce site Web utilise des témoins et des services analytiques",
              },
              {
                title: "Essentiel",
                description:
                  "Ce site Web utilise des témoins et des services essentiels",
              },
            ]);
          });
        });
      });
    });
    describe("experience translation overrides", () => {
      describe("when set via window obj", () => {
        describe("when fides_override_language exactly matches experience locale", () => {
          beforeEach(() => {
            visitDemoWithI18n({
              navigatorLanguage: ENGLISH_LOCALE,
              globalPrivacyControl: true,
              fixture: "experience_banner_modal.json",
            });
          });
          it("applies experience language overrides", () => {
            const experienceTranslationOverrides = {
              fides_title: "My override title",
              fides_description: "My override description",
              fides_privacy_policy_url: "https://example.com/privacy",
              fides_override_language: "en",
            };
            cy.fixture("consent/experience_banner_modal.json").then(
              (experience) => {
                const experienceItem = experience.items[0];
                const translation: ExperienceConfigTranslation =
                  experienceItem.experience_config.translations.filter(
                    (i: ExperienceConfigTranslation) => i.language === "en",
                  )[0];
                stubConfig(
                  {
                    options: {
                      customOptionsPath: TEST_OVERRIDE_WINDOW_PATH,
                    },
                    experience: experienceItem,
                  },
                  null,
                  null,
                  undefined,
                  { ...experienceTranslationOverrides },
                );
                cy.get("div#fides-banner").within(() => {
                  cy.get(".fides-banner-title")
                    .first()
                    .contains(translation.banner_title as string);
                  cy.get(
                    "div#fides-banner-description.fides-banner-description",
                  ).contains(translation.banner_description as string);
                  cy.get("#fides-privacy-policy-link a").should(
                    "have.attr",
                    "href",
                    experienceTranslationOverrides.fides_privacy_policy_url,
                  );
                });
                // Open the modal
                cy.contains("button", "Manage preferences").click();
                cy.get("div#fides-modal").within(() => {
                  cy.get(".fides-modal-title").contains(
                    experienceTranslationOverrides.fides_title,
                  );
                  cy.get(".fides-modal-description").contains(
                    experienceTranslationOverrides.fides_description,
                  );
                });
              },
            );
          });
        });

        describe("when fides_override_language is only part of an experience locale string", () => {
          beforeEach(() => {
            visitDemoWithI18n({
              navigatorLanguage: FRENCH_LOCALE,
              globalPrivacyControl: true,
              fixture: "experience_banner_modal.json",
            });
          });
          // TODO (PROD-1885): matchLocale needs to support partial language match
          it.skip("applies experience language overrides", () => {
            const experienceTranslationOverrides = {
              fides_title: "My French override title",
              fides_description: "My French override description",
              fides_privacy_policy_url: "https://example.com/privacy-french",
              fides_override_language: "fr",
            };
            cy.fixture("consent/experience_banner_modal.json").then(
              (experience) => {
                const experienceItem = experience.items[0];
                const translation: ExperienceConfigTranslation =
                  experienceItem.experience_config.translations.filter(
                    (i: ExperienceConfigTranslation) => i.language === "fr-CA",
                  )[0];
                stubConfig(
                  {
                    options: {
                      customOptionsPath: TEST_OVERRIDE_WINDOW_PATH,
                    },
                    experience: experienceItem,
                  },
                  null,
                  null,
                  undefined,
                  { ...experienceTranslationOverrides },
                );
                cy.get("div#fides-banner").within(() => {
                  cy.get(".fides-banner-title")
                    .first()
                    .contains(translation.banner_title as string);
                  cy.get(
                    "div#fides-banner-description.fides-banner-description",
                  ).contains(translation.banner_description as string);
                  cy.get("#fides-privacy-policy-link a").should(
                    "have.attr",
                    "href",
                    experienceTranslationOverrides.fides_privacy_policy_url,
                  );
                });
                // Open the modal
                cy.contains("button", "Manage preferences").click();
                cy.get("div#fides-modal").within(() => {
                  cy.get(".fides-modal-title").contains(
                    experienceTranslationOverrides.fides_title,
                  );
                  cy.get(".fides-modal-description").contains(
                    experienceTranslationOverrides.fides_description,
                  );
                });
              },
            );
          });
        });

        describe("when fides_override_language is in a locale that does not exist in experience translations", () => {
          beforeEach(() => {
            visitDemoWithI18n({
              navigatorLanguage: JAPANESE_LOCALE,
              globalPrivacyControl: true,
              fixture: "experience_banner_modal.json",
            });
          });
          it("does not apply experience translation overrides", () => {
            const experienceTranslationOverrides = {
              fides_title: "My override title",
              fides_description: "My override description",
              fides_override_language: "ja",
            };
            cy.fixture("consent/experience_banner_modal.json").then(
              (experience) => {
                const experienceItem = experience.items[0];
                // we expect to default to english translation
                const translation: ExperienceConfigTranslation =
                  experienceItem.experience_config.translations.filter(
                    (i: ExperienceConfigTranslation) => i.language === "en",
                  )[0];
                stubConfig(
                  {
                    options: {
                      customOptionsPath: TEST_OVERRIDE_WINDOW_PATH,
                    },
                    experience: experienceItem,
                  },
                  null,
                  null,
                  undefined,
                  { ...experienceTranslationOverrides },
                );
                cy.get("div#fides-banner").within(() => {
                  cy.get(".fides-banner-title")
                    .first()
                    .contains(translation.banner_title as string);
                  cy.get(
                    "div#fides-banner-description.fides-banner-description",
                  ).contains(translation.banner_description as string);
                });
                // Open the modal
                cy.contains("button", "Manage preferences").click();
                cy.get("div#fides-modal").within(() => {
                  cy.get(".fides-modal-title").contains(
                    translation.title as string,
                  );
                  cy.get(".fides-modal-description").contains(
                    translation.description as string,
                  );
                });
              },
            );
          });
          it("does apply fides_privacy_policy_url override", () => {
            const experienceTranslationOverrides = {
              fides_privacy_policy_url: "https://example.com/privacy",
              fides_override_language: "ja",
            };
            cy.fixture("consent/experience_banner_modal.json").then(
              (experience) => {
                const experienceItem = experience.items[0];
                stubConfig(
                  {
                    options: {
                      customOptionsPath: TEST_OVERRIDE_WINDOW_PATH,
                    },
                    experience: experienceItem,
                  },
                  null,
                  null,
                  undefined,
                  { ...experienceTranslationOverrides },
                );
                cy.get("div#fides-banner").within(() => {
                  cy.get("#fides-privacy-policy-link a").should(
                    "have.attr",
                    "href",
                    experienceTranslationOverrides.fides_privacy_policy_url as string,
                  );
                });
              },
            );
          });
        });

        describe("when fides_override_language is not provided", () => {
          beforeEach(() => {
            visitDemoWithI18n({
              navigatorLanguage: ENGLISH_LOCALE,
              globalPrivacyControl: true,
              fixture: "experience_banner_modal.json",
            });
          });
          it("does not apply experience translation overrides", () => {
            const experienceTranslationOverrides = {
              fides_title: "My override title",
              fides_description: "My override description",
              // skips setting fides_override_language
            };
            cy.fixture("consent/experience_banner_modal.json").then(
              (experience) => {
                const experienceItem = experience.items[0];
                const translation: ExperienceConfigTranslation =
                  experienceItem.experience_config.translations.filter(
                    (i: ExperienceConfigTranslation) => i.language === "en",
                  )[0];
                stubConfig(
                  {
                    options: {
                      customOptionsPath: TEST_OVERRIDE_WINDOW_PATH,
                    },
                    experience: experienceItem,
                  },
                  null,
                  null,
                  undefined,
                  { ...experienceTranslationOverrides },
                );
                cy.get("div#fides-banner").within(() => {
                  cy.get(".fides-banner-title")
                    .first()
                    .contains(translation.banner_title as string);
                  cy.get(
                    "div#fides-banner-description.fides-banner-description",
                  ).contains(translation.banner_description as string);
                });
                // Open the modal
                cy.contains("button", "Manage preferences").click();
                cy.get("div#fides-modal").within(() => {
                  cy.get(".fides-modal-title").contains(
                    translation.title as string,
                  );
                  cy.get(".fides-modal-description").contains(
                    translation.description as string,
                  );
                });
              },
            );
          });
          it("does apply fides_privacy_policy_url override", () => {
            const experienceTranslationOverrides = {
              fides_privacy_policy_url: "https://example.com/privacy",
            };
            cy.fixture("consent/experience_banner_modal.json").then(
              (experience) => {
                const experienceItem = experience.items[0];
                stubConfig(
                  {
                    options: {
                      customOptionsPath: TEST_OVERRIDE_WINDOW_PATH,
                    },
                    experience: experienceItem,
                  },
                  null,
                  null,
                  undefined,
                  { ...experienceTranslationOverrides },
                );
                cy.get("div#fides-banner").within(() => {
                  cy.get("#fides-privacy-policy-link a").should(
                    "have.attr",
                    "href",
                    experienceTranslationOverrides.fides_privacy_policy_url as string,
                  );
                });
              },
            );
          });
        });
      });
    });
  });

  /**********************************************************
   *
   * FIDESJS TCF BANNER + MODAL TESTS
   *
   **********************************************************/
  describe("when localizing tcf_overlay components", () => {
    const testTcfBannerLocalization = (t: TestTcfBannerTranslations) => {
      cy.get("#fides-banner").within(() => {
        cy.get(".fides-banner-title").contains(t.banner_title);
        cy.get(".fides-banner-description").contains(t.banner_description);
        cy.get("#fides-button-group").contains(
          t.privacy_preferences_link_label,
        );
        cy.get("#fides-button-group").contains(t.reject_button_label);
        cy.get("#fides-button-group").contains(t.accept_button_label);
        cy.getByTestId("fides-banner-subtitle").contains(t.purpose_header);
        cy.getByTestId("fides-tcf-banner-supplemental").contains(
          t.purpose_example,
        );

        // Privacy policy link is optional; if provided, check that it is localized
        if (t.privacy_policy_link_label) {
          cy.get("#fides-privacy-policy-link").contains(
            t.privacy_policy_link_label,
          );
          cy.get("#fides-privacy-policy-link a").should(
            "have.attr",
            "href",
            t.privacy_policy_url,
          );
        } else {
          cy.get("#fides-privacy-policy-link").should("not.exist");
        }
      });
    };

    const testTcfModalPurposesTabLocalization = (
      t: TestTcfModalTranslations,
    ) => {
      cy.get("#fides-panel-purposes").within(() => {
        // Check the right tab is visible, the overall description, and radio buttons
        cy.get(".fides-info-box").should("be.visible");
        cy.get(".fides-info-box").contains(t.purposes_description);
        cy.get(".fides-radio-button-group button").then((buttons) => {
          cy.wrap(buttons[0]).contains(t.consent);
          cy.wrap(buttons[1]).contains(t.legint);
        });

        // Check the list of Purposes and toggle open a single example to check illustrations, etc.
        cy.getByTestId("records-list-purposes").within(() => {
          cy.get(".fides-record-header").contains(t.purposes);
          cy.get(".fides-notice-toggle").contains(t.purpose_example).click();
          cy.get(".fides-disclosure-visible").contains(
            t.purpose_example_description,
          );
          cy.get(".fides-disclosure-visible .fides-tcf-illustration").contains(
            t.purpose_example_illustration,
          );
          cy.get(
            ".fides-disclosure-visible .fides-tcf-toggle-content:last",
          ).within(() => {
            cy.contains(t.vendors);
          });
        });

        // Check the list of Special purposes and toggle open a single example to check illustrations, etc.
        cy.getByTestId("records-list-specialPurposes").within(() => {
          cy.get(".fides-record-header").contains(t.special_purposes);
          cy.get(".fides-notice-toggle")
            .contains(t.special_purpose_example)
            .click();
          cy.get(".fides-disclosure-visible").contains(
            t.special_purpose_example_description,
          );
          cy.get(".fides-disclosure-visible .fides-tcf-illustration").contains(
            t.special_purpose_example_illustration,
          );
          cy.get(
            ".fides-disclosure-visible .fides-tcf-toggle-content:last",
          ).within(() => {
            cy.contains(t.vendors);
          });
        });
      });
    };

    const testTcfModalFeaturesTabLocalization = (
      t: TestTcfModalTranslations,
    ) => {
      cy.get("#fides-panel-features").within(() => {
        // Check the right tab is visible and the overall description
        cy.get(".fides-info-box").should("be.visible");
        cy.get(".fides-info-box").contains(t.features_description);

        // Check the list of Features and toggle open a single example
        cy.getByTestId("records-list-features").within(() => {
          cy.get(".fides-record-header").contains(t.features);
          cy.get(".fides-notice-toggle").contains(t.feature_example).click();
          cy.get(".fides-disclosure-visible").contains(
            t.feature_example_description,
          );
          cy.get(
            ".fides-disclosure-visible .fides-tcf-toggle-content:last",
          ).within(() => {
            cy.contains(t.vendors);
          });
        });

        // Check the list of Special features and toggle open a single example to check illustrations, etc.
        cy.getByTestId("records-list-specialFeatures").within(() => {
          cy.get(".fides-record-header").contains(t.special_features);
          cy.get(".fides-notice-toggle")
            .contains(t.special_feature_example)
            .click();
          cy.get(".fides-disclosure-visible").contains(
            t.special_feature_example_description,
          );
          cy.get(
            ".fides-disclosure-visible .fides-tcf-toggle-content:last",
          ).within(() => {
            cy.contains(t.vendors);
          });
        });
      });
    };

    const testTcfModalVendorsTabLocalization = (
      t: TestTcfModalTranslations,
    ) => {
      cy.get("#fides-panel-vendors").within(() => {
        // Check the right tab is visible, the overall description, and radio buttons
        cy.get(".fides-info-box").should("be.visible");
        cy.get(".fides-info-box").contains(t.vendors_description);
        cy.get(".fides-radio-button-group button").then((buttons) => {
          cy.wrap(buttons[0]).contains(t.consent);
          cy.wrap(buttons[1]).contains(t.legint);
        });

        // Check the list of IAB TCF vendors and toggle open a single example
        cy.getByTestId("records-list-vendors").within(() => {
          cy.get(".fides-record-header").contains(t.vendors_iab);
          cy.get(".fides-notice-badge").contains("IAB TCF");
          cy.get(".fides-notice-toggle").contains(t.vendor_iab_example).click();
          cy.get(".fides-disclosure-visible").within(() => {
            cy.get("p").contains(t.vendor_iab_example_description);
            cy.get("a.fides-external-link").then((links) => {
              cy.wrap(links[0]).contains(t.vendor_privacy_policy);
              cy.wrap(links[1]).contains(t.vendor_legint_disclosure);
            });
            cy.get(".fides-vendor-details-table").then((tables) => {
              cy.wrap(tables[0]).within(() => {
                cy.get("thead").contains(t.purposes);
                cy.get("thead").contains(t.retention);
                cy.get("tr").contains(t.purpose_example);
              });
              cy.wrap(tables[1]).within(() => {
                cy.get("thead").contains(t.special_purposes);
                cy.get("thead").contains(t.retention);
                cy.get("tr").contains(t.special_purpose_example);
              });
              cy.wrap(tables[2]).within(() => {
                cy.get("thead").contains(t.data_categories);
              });
            });
          });
        });

        // Toggle over to Legitimate interest vendors to view Other
        cy.get(".fides-radio-button-group button").contains(t.legint).click();

        // Check the list of Other vendors and toggle open a single example
        cy.getByTestId("records-list-vendors").within(() => {
          cy.get(".fides-record-header").contains(t.vendors_other);
          cy.get(".fides-notice-badge").should("not.exist");
          cy.get(".fides-notice-toggle")
            .contains(t.vendor_other_example)
            .click();
          cy.get(".fides-disclosure-visible").within(() => {
            cy.get("p").contains(t.vendor_other_example_description);
            cy.get(".fides-vendor-details-table").then((tables) => {
              cy.wrap(tables[0]).within(() => {
                cy.get("thead").contains(t.purposes);
                cy.get("thead").contains(t.retention);
              });
              cy.wrap(tables[1]).within(() => {
                cy.get("thead").contains(t.special_purposes);
                cy.get("thead").contains(t.retention);
                cy.get("tr").contains(t.special_purpose_example);
              });
              cy.wrap(tables[2]).within(() => {
                cy.get("thead").contains(t.features);
              });
            });
          });
        });
      });
    };

    const testTcfModalLocalization = (t: TestTcfModalTranslations) => {
      // Start by opening the modal
      // NOTE: We could also use cy.get("#fides-modal-link").click(), but let's
      // assume the banner is visible in these tests
      cy.get("#fides-banner .fides-manage-preferences-button").click();
      cy.get("#fides-modal").should("be.visible");

      // Check modal localization
      cy.get("#fides-modal").within(() => {
        cy.get(".fides-modal-title").contains(t.title);
        cy.get(".fides-modal-description").contains(t.description);
        cy.get(".fides-modal-button-group").contains(t.save_button_label);
        cy.get(".fides-modal-button-group").contains(t.reject_button_label);
        cy.get(".fides-modal-button-group").contains(t.accept_button_label);

        // Check each of the modal tabs
        cy.get(".fides-tabs .fides-tab-list li").then((items) => {
          cy.wrap(items[0]).contains(t.purposes).click();
          testTcfModalPurposesTabLocalization(t);
          cy.wrap(items[1]).contains(t.features).click();
          testTcfModalFeaturesTabLocalization(t);
          cy.wrap(items[2]).contains(t.vendors).click();
          testTcfModalVendorsTabLocalization(t);
        });

        // Privacy policy link is optional; if provided, check that it is localized
        if (t.privacy_policy_link_label) {
          cy.get("#fides-privacy-policy-link").contains(
            t.privacy_policy_link_label,
          );
          cy.get("#fides-privacy-policy-link a").should(
            "have.attr",
            "href",
            t.privacy_policy_url,
          );
        } else {
          cy.get("#fides-privacy-policy-link").should("not.exist");
        }
      });
    };

    /**
     * Define our parameterized test cases to generate specs below!
     */
    const tests = [
      {
        navigatorLanguage: ENGLISH_LOCALE,
        locale: ENGLISH_LOCALE,
        banner: ENGLISH_TCF_BANNER,
        modal: ENGLISH_TCF_MODAL,
      },
      {
        navigatorLanguage: SPANISH_LOCALE,
        locale: SPANISH_LOCALE,
        banner: SPANISH_TCF_BANNER,
        modal: SPANISH_TCF_MODAL,
      },
    ];

    tests.forEach(({ navigatorLanguage, locale, banner, modal }) => {
      it(`localizes tcf_overlay components in the correct locale (${locale})`, () => {
        visitDemoWithI18n({
          navigatorLanguage,
          globalPrivacyControl: true,
          options: { tcfEnabled: true },
        });
        testTcfBannerLocalization(banner);
        if (locale === SPANISH_LOCALE) {
          cy.wait("@getGvlTranslations");
        }
        testTcfModalLocalization(modal);
      });
    });
    describe("when user selects their own locale", () => {
      it(`localizes in the user selected locale (${SPANISH_LOCALE})`, () => {
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          options: { tcfEnabled: true },
        });
        cy.get("#fides-banner").should("be.visible");
        cy.get(
          `#fides-banner [data-testid='fides-i18n-option-${SPANISH_LOCALE}']`,
        ).focus();
        cy.get(`.fides-i18n-menu`).focused().click();
        cy.wait("@getGvlTranslations").then((interception) => {
          const { url } = interception.request;
          expect(url.split("?")[1]).to.eq(`language=${SPANISH_LOCALE}`);
        });
        testTcfBannerLocalization(SPANISH_TCF_BANNER);
        testTcfModalLocalization(SPANISH_TCF_MODAL);
      });
    });
    describe("when translations API fails", () => {
      beforeEach(() => {
        cy.intercept(
          {
            method: "GET",
            url: `${API_URL}${FidesEndpointPaths.GVL_TRANSLATIONS}*`,
            middleware: true,
          },
          (req) => {
            req.on("before:response", (res) => {
              res.send(500, { error: "Internal Server Error" });
            });
          },
        ).as("getGvlTranslations500");
      });
      it("falls back to default locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: FRENCH_LOCALE,
          options: { tcfEnabled: true },
        });
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("fides-tcf-banner-supplemental").contains(
          ENGLISH_TCF_BANNER.purpose_example,
        ); // english fallback
      });
    });
  });

  describe("when localizing privacy_center components", () => {
    const GEOLOCATION_API_URL = "https://www.example.com/location";
    const VERIFICATION_CODE = "112358";
    const SETTINGS = {
      IS_OVERLAY_ENABLED: true,
      IS_GEOLOCATION_ENABLED: true,
      GEOLOCATION_API_URL,
    };

    const beforeAll = () => {
      cy.clearAllCookies();

      // Seed local storage with verification data
      cy.window().then((win) => {
        win.localStorage.setItem(
          "consentRequestId",
          JSON.stringify("consent-request-id"),
        );
        win.localStorage.setItem(
          "verificationCode",
          JSON.stringify(VERIFICATION_CODE),
        );
      });

      // Enable GPC
      cy.on("window:before:load", (win) => {
        // eslint-disable-next-line no-param-reassign
        win.navigator.globalPrivacyControl = true;
      });

      // Intercept consent request
      cy.intercept("POST", `${API_URL}/consent-request`, {
        body: {
          consent_request_id: "consent-request-id",
        },
      }).as("postConsentRequest");

      // Intercept sending identity data to the backend to access /consent page
      cy.intercept(
        "POST",
        `${API_URL}/consent-request/consent-request-id/verify`,
        { fixture: "consent/verify" },
      ).as("postConsentRequestVerify");

      // Location intercept
      cy.intercept("GET", GEOLOCATION_API_URL, {
        fixture: "consent/geolocation.json",
      }).as("getGeolocation");

      // Patch privacy preference intercept
      cy.intercept(
        "PATCH",
        `${API_URL}/consent-request/consent-request-id/privacy-preferences*`,
        {
          fixture: "consent/privacy_preferences.json",
        },
      ).as("patchPrivacyPreference");

      // Experience intercept
      cy.intercept("GET", `${API_URL}/privacy-experience/*`, {
        fixture: "consent/experience_privacy_center.json",
      }).as("getExperience");
    };

    describe("displays localized texts", () => {
      beforeEach(() => {
        beforeAll();
        cy.visitWithLanguage("/consent", SPANISH_LOCALE);
        cy.getByTestId("consent");
        cy.overrideSettings(SETTINGS);
        cy.wait("@getExperience");
      });

      it("displays localized text from experience", () => {
        cy.getByTestId("consent-heading").contains(SPANISH_MODAL.title);
        cy.getByTestId("consent-description").contains(
          SPANISH_MODAL.description,
        );
      });

      it("displays localized text for gpc banner", () => {
        cy.getByTestId("gpc.banner.title").contains(SPANISH_MODAL.gpc_title);
        cy.getByTestId("gpc.banner.description").contains(
          SPANISH_MODAL.gpc_description,
        );
      });

      it("displays localized save button", () => {
        cy.getByTestId("save-btn").contains(SPANISH_MODAL.save_button_label);
      });

      it("displays localized privacy policy", () => {
        cy.getByTestId("privacypolicy.link").contains(
          SPANISH_MODAL.privacy_policy_link_label!,
        );
        cy.getByTestId("privacypolicy.link")
          .should("have.attr", "href")
          .and("include", SPANISH_MODAL.privacy_policy_url!);
      });

      it("displays localized notice texts", () => {
        cy.getByTestId("consent-item-pri_notice-analytics-000").contains(
          SPANISH_NOTICES[1].title,
        );
        cy.getByTestId("consent-item-pri_notice-analytics-000").contains(
          SPANISH_NOTICES[1].description,
        );
      });
    });

    const EXPECTED_NOTICE_HISTORY_IDS = [
      "pri_notice-history-advertising-es-000", // Spanish (es)
      "pri_notice-history-analytics-es-000", // Spanish (es)
      "pri_notice-history-essential-es-000", // Spanish (es)
    ];

    const EXPECTED_EXPERIENCE_CONFIG_HISTORY_ID =
      "pri_exp-history-privacy-center-es-000";

    describe("utilizes correct history and configs id for the current language", () => {
      beforeEach(() => {
        beforeAll();

        // Consent reporting intercept
        cy.intercept(
          "PATCH",
          `${API_URL}/consent-request/consent-request-id/notices-served`,
          { fixture: "consent/notices_served.json" },
        ).as("patchNoticesServed");

        cy.visitWithLanguage("/", SPANISH_LOCALE);
        cy.wait("@getVerificationConfig");
        cy.overrideSettings(SETTINGS);
        cy.wait("@getExperience");
        cy.getByTestId("card").contains("Manage your consent").click();
        cy.getByTestId("consent-request-form").within(() => {
          cy.get("input#email").type("test@example.com");
          cy.get("button").contains("Continue").click();
        });
        cy.wait("@postConsentRequest");

        cy.getByTestId("verification-form").within(() => {
          cy.get("input").type(VERIFICATION_CODE);
          cy.get("button").contains("Submit code").click();
        });
        cy.wait("@postConsentRequestVerify");
      });

      it("calls notices served with the correct history id for the notices", () => {
        cy.wait("@patchNoticesServed").then((interception) => {
          expect(interception.request.body.privacy_notice_history_ids).to.eql(
            EXPECTED_NOTICE_HISTORY_IDS,
          );
        });
      });

      it("calls notices served with the correct history id for the experience config", () => {
        cy.wait("@patchNoticesServed").then((interception) => {
          expect(
            interception.request.body.privacy_experience_config_history_id,
          ).to.eql(EXPECTED_EXPERIENCE_CONFIG_HISTORY_ID);
        });
      });

      it("calls privacy preference with the correct history id for the experience config", () => {
        cy.getByTestId("save-btn").click();
        cy.wait("@patchPrivacyPreference").then((interception) => {
          const {
            preferences,
            privacy_experience_config_history_id:
              privacyExperienceConfigHistoryId,
          } = interception.request.body;

          expect(privacyExperienceConfigHistoryId).to.eql(
            EXPECTED_EXPERIENCE_CONFIG_HISTORY_ID,
          );
          expect(
            preferences.map((p: any) => p.privacy_notice_history_id),
          ).to.eql(EXPECTED_NOTICE_HISTORY_IDS);
        });
      });
    });
  });

  /**
   * Special-case tests for the On/Off toggle labels, which are hidden in non-English locales
   */
  describe("when localizing the On/Off toggle labels", () => {
    describe(`when in the default locale (${ENGLISH_LOCALE})`, () => {
      it("shows the On/Off toggle labels in banner_and_modal components", () => {
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          fixture: "experience_banner_modal.json",
        });
        cy.get("#fides-modal-link").click();
        cy.get("#fides-modal .fides-modal-notices").within(() => {
          cy.get(".fides-toggle:first").contains("Off");
          cy.get(".fides-toggle:first").click();
          cy.get(".fides-toggle:first").contains("On");
        });
      });

      it("shows the On/Off toggle labels in tcf_overlay components", () => {
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          options: { tcfEnabled: true },
        });
        cy.get("#fides-modal-link").click();
        cy.getByTestId("records-list-purposes").within(() => {
          cy.get(".fides-toggle:first").contains("Off");
          cy.get(".fides-toggle:first").click();
          cy.get(".fides-toggle:first").contains("On");
        });
      });
    });

    describe(`when in any non-default locale (${SPANISH_LOCALE})`, () => {
      it("hides the On/Off toggle labels in banner_and_modal components", () => {
        visitDemoWithI18n({
          navigatorLanguage: SPANISH_LOCALE,
          fixture: "experience_banner_modal.json",
        });
        cy.get("#fides-modal-link").click();
        cy.get("#fides-modal .fides-modal-notices").within(() => {
          cy.get(".fides-toggle:first").contains("Off").should("not.exist");
          cy.get(".fides-toggle:first").click();
          cy.get(".fides-toggle:first").contains("On").should("not.exist");
        });
      });

      it("hides the On/Off toggle labels in tcf_overlay components", () => {
        visitDemoWithI18n({
          navigatorLanguage: SPANISH_LOCALE,
          options: { tcfEnabled: true },
        });
        cy.get("#fides-modal-link").click();
        cy.getByTestId("records-list-purposes").within(() => {
          cy.get(".fides-toggle:first").contains("Off").should("not.exist");
          cy.get(".fides-toggle:first").click();
          cy.get(".fides-toggle:first").contains("On").should("not.exist");
        });
      });
    });
  });
});
