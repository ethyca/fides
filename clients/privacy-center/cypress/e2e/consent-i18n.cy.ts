import { FidesOptions, PrivacyExperience, PrivacyNotice } from "fides-js";
import { stubConfig } from "../support/stubs";

describe("Consent i18n", () => {
  /**
   * Define (lots of) reusable test data for all the specs below!
   */
  const ENGLISH_LOCALE = "en-US";
  const SPANISH_LOCALE = "es";
  const JAPANESE_LOCALE = "ja-JP";
  type TestFixture =
    | "experience_banner_modal.json"
    | "experience_banner_modal_notice_only.json"
    | "experience_tcf.json"
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
    privacy_policy_link_label: string | null;
    privacy_policy_url: string | null;
  };

  type TestNoticeTranslations = {
    title: string;
    description: string;
  };

  type TestTcfBannerTranslations = TestBannerTranslations & {
    vendors_count: string;
    vendors_consent_count: string;
    vendors_legint_count: string;
    tcf_stacks: { title: string; description: string, isStacked?: boolean }[];
    purposes: string;
    purposes_include: string;
    stacked_purpose_example: string;
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
    special_features: string;
    vendors: string;
    vendors_description: string;
    vendors_we_use: string;
    vendor_example: string;
    consent: string;
    legint: string;
  };

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
    privacy_policy_link_label: "Privacy Policy",
    privacy_policy_url: "https://privacy.example.com/",
  };

  const ENGLISH_NOTICES: TestNoticeTranslations[] = [
    { title: "Advertising", description: "This website uses marketing" },
    { title: "Analytics", description: "This website uses analytics" },
    { title: "Essential", description: "This website uses essential" },
  ];

  const ENGLISH_TCF_BANNER: TestTcfBannerTranslations = {
    ...ENGLISH_BANNER, 
    ...{
      vendors_count: "Vendors",
      vendors_consent_count: "Vendors using consent",
      vendors_legint_count: "Vendors using legitimate interest",
      tcf_stacks: [
        { title: "Selection of personalised advertising", description: "Advertising can be personalised", isStacked: true },
        { title: "Use profiles to select", description: "Content presented to you" },
        { title: "Use precise geolocation", description: "With your acceptance, your precise location" },
      ],
      purposes: "Purposes",
      purposes_include: "Purposes include",
      stacked_purpose_example: "Purpose 2: Use limited data to select",
    },
  };

  const ENGLISH_TCF_MODAL: TestTcfModalTranslations = {
    ...ENGLISH_MODAL,
    ...{
      purposes: "Purposes",
      purposes_description: "Below, you will find a list of the purposes",
      purpose_example: "Use profiles to select personalised advertising",
      purpose_example_description: "Advertising presented to you on this service",
      purpose_example_illustration: "An online retailer wants to advertise",
      special_purposes: "Special purposes",
      special_purpose_example: "Ensure security",
      special_purpose_example_description: "Your data can be used to monitor",
      special_purpose_example_illustration: "An advertising intermediary delivers ads",
      features: "Features",
      features_description: "Below, you will find a list of the features",
      special_features: "Special features",
      vendors: "Vendors",
      vendors_description: "Below, you will find a list of vendors",
      vendors_we_use: "Vendors we use",
      vendor_example: "Captify",
      consent: "Consent",
      legint: "Legitimate interest",
    }
  }

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

  // Setup a test case with the given params
  const visitDemoWithI18n = (props: {
    navigatorLanguage: string;
    fixture: TestFixture;
    globalPrivacyControl?: boolean;
    options?: Partial<FidesOptions>;
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
    cy.fixture(`consent/${props.fixture}`).then((data) => {
      let experience = data.items[0];
      cy.log(`Using PrivacyExperience data from ${props.fixture}`, experience);
      if (props.overrideExperience) {
        experience = props.overrideExperience(experience);
        cy.log(
          "Using overridden PrivacyExperience data from overrideExperience()",
          experience
        );
      }
      stubConfig(
        { experience, options: props.options },
        null,
        null,
        props.queryParams
      );
    });
    cy.window().its("navigator.language").should("eq", props.navigatorLanguage);
  };

  // Reusable assertions to test that the banner component localizes correctly
  const testBannerLocalization = (expected: TestBannerTranslations) => {
    /**
     * Check banner localization
     *
     * NOTE: These checks will not pass on a "notice-only" banner variant, since
     * many of the buttons are not seen there. See the dedicated notice-only
     * specs for those tests instead!
     */
    cy.get("#fides-banner").within(() => {
      cy.get(".fides-banner-title").contains(expected.banner_title);
      cy.get(".fides-banner-description").contains(expected.banner_description);
      cy.get("#fides-button-group").contains(
        expected.privacy_preferences_link_label
      );
      cy.get("#fides-button-group").contains(expected.reject_button_label);
      cy.get("#fides-button-group").contains(expected.accept_button_label);
      cy.get(".fides-gpc-label").contains(expected.gpc_label);
      cy.get(".fides-gpc-label .fides-gpc-badge").contains(
        expected.gpc_status_label
      );

      // Privacy policy link is optional; if provided, check that it is localized
      if (expected.privacy_policy_link_label) {
        cy.get("#fides-privacy-policy-link").contains(
          expected.privacy_policy_link_label
        );
        cy.get("#fides-privacy-policy-link a").should(
          "have.attr",
          "href",
          expected.privacy_policy_url
        );
      } else {
        cy.get("#fides-privacy-policy-link").should("not.exist");
      }
    });
  };

  // Reusable assertions to test that the modal component localizes correctly
  const openAndTestModalLocalization = (expected: TestModalTranslations) => {
    // Start by opening the modal
    // NOTE: We could also use cy.get("#fides-modal-link").click(), but let's
    // assume the banner is visible in these tests
    cy.get("#fides-banner .fides-manage-preferences-button").click();
    cy.get("#fides-modal").should("be.visible");

    // Check modal localization
    cy.get("#fides-modal").within(() => {
      cy.get(".fides-modal-title").contains(expected.title);
      cy.get(".fides-modal-description").contains(expected.description);
      cy.get(".fides-modal-button-group").contains(expected.save_button_label);
      cy.get(".fides-modal-button-group").contains(
        expected.reject_button_label
      );
      cy.get(".fides-modal-button-group").contains(
        expected.accept_button_label
      );
      cy.get(".fides-gpc-banner .fides-gpc-header").contains(
        expected.gpc_title
      );
      cy.get(".fides-gpc-banner").contains(expected.gpc_title);

      // Privacy policy link is optional; if provided, check that it is localized
      if (expected.privacy_policy_link_label) {
        cy.get("#fides-privacy-policy-link").contains(
          expected.privacy_policy_link_label
        );
        cy.get("#fides-privacy-policy-link a").should(
          "have.attr",
          "href",
          expected.privacy_policy_url
        );
      } else {
        cy.get("#fides-privacy-policy-link").should("not.exist");
      }
    });
  };

  // Reusable assertions to test that the modal notices component localizes correctly
  const testModalNoticesLocalization = (expected: TestNoticeTranslations[]) => {
    // Check modal notices localization
    cy.get("#fides-modal .fides-modal-notices").within(() => {
      expected.forEach((notice) => {
        cy.get(".fides-notice-toggle-title").contains(notice.title).click();
        cy.get(".fides-disclosure-visible").contains(notice.description);
        cy.get(".fides-notice-toggle-title").contains(notice.title).click();
      });
    });
  };

  // Reusable assertions to test that the modal notices component localizes correctly
  const testTcfBannerStacksLocalization = (expected: TestTcfBannerTranslations) => {
    // Check banner stacks localization
    cy.get(".fides-tcf-stacks-container").within(() => {
      expected.tcf_stacks.forEach(({title, description, isStacked}) => {
        cy.get(".fides-notice-toggle-title").contains(title).click();
        cy.get(".fides-disclosure-visible").contains(description);
        // If this is truly a "stack", check the additional purposes list
        if (isStacked) {
          cy.get(".fides-disclosure-visible .fides-tcf-purpose-vendor-title").contains(expected.purposes_include);
          cy.get(".fides-disclosure-visible .fides-tcf-purpose-vendor-list").contains(expected.stacked_purpose_example);
        }
        cy.get(".fides-notice-toggle-title").contains(title).click();
      });
    });
  };

  const testTcfBannerLocalization = (expected: TestTcfBannerTranslations) => {
    cy.get("#fides-banner").within(() => {
      cy.get(".fides-banner-title").contains(expected.banner_title);
      cy.get(".fides-banner-description").contains(expected.banner_description);
      cy.get("#fides-button-group").contains(
        expected.privacy_preferences_link_label
      );
      cy.get("#fides-button-group").contains(expected.reject_button_label);
      cy.get("#fides-button-group").contains(expected.accept_button_label);
      cy.get(".fides-vendor-info-banner .fides-vendor-info-label").contains(expected.vendors_count);
      cy.get(".fides-vendor-info-banner .fides-vendor-info-label").contains(expected.vendors_consent_count);
      cy.get(".fides-vendor-info-banner .fides-vendor-info-label").contains(expected.vendors_legint_count);

      testTcfBannerStacksLocalization(ENGLISH_TCF_BANNER);

      // Privacy policy link is optional; if provided, check that it is localized
      if (expected.privacy_policy_link_label) {
        cy.get("#fides-privacy-policy-link").contains(
          expected.privacy_policy_link_label
        );
        cy.get("#fides-privacy-policy-link a").should(
          "have.attr",
          "href",
          expected.privacy_policy_url
        );
      } else {
        cy.get("#fides-privacy-policy-link").should("not.exist");
      }
    });
  };

  const testTcfModalPurposesTabLocalization = (expected: TestTcfModalTranslations) => {
    cy.get("#fides-panel-Purposes").within(() => {
      cy.get(".fides-info-box").should("be.visible");
      cy.get(".fides-info-box").contains(expected.purposes_description);
      cy.get(".fides-radio-button-group button").then(buttons => {
        cy.wrap(buttons[0]).contains(expected.consent);
        cy.wrap(buttons[1]).contains(expected.legint);
      });

      cy.getByTestId("records-list-Purposes").within(() => {
        cy.get(".fides-record-header").contains(expected.purposes);
        cy.get(".fides-notice-toggle").contains(expected.purpose_example).click();
        cy.get(".fides-disclosure-visible").contains(expected.purpose_example_description);
        cy.get(".fides-disclosure-visible .fides-tcf-illustration").contains(expected.purpose_example_illustration);
        cy.get(".fides-disclosure-visible .fides-tcf-toggle-content:last").within(() => {
          cy.contains(expected.vendors_we_use);
          cy.get("li").contains(expected.vendor_example);
        });
      });

      cy.getByTestId("records-list-Special purposes").within(() => {
        cy.get(".fides-record-header").contains(expected.special_purposes);
        cy.get(".fides-notice-toggle").contains(expected.special_purpose_example).click();
        cy.get(".fides-disclosure-visible").contains(expected.special_purpose_example_description);
        cy.get(".fides-disclosure-visible .fides-tcf-illustration").contains(expected.special_purpose_example_illustration);
        cy.get(".fides-disclosure-visible .fides-tcf-toggle-content:last").within(() => {
          cy.contains(expected.vendors_we_use);
          cy.get("li").contains(expected.vendor_example);
        });
      });
    });
  };

  const testTcfModalFeaturesTabLocalization = (expected: TestTcfModalTranslations) => {
    cy.get("#fides-panel-Features").within(() => {
      cy.get(".fides-info-box").should("be.visible");
      cy.get(".fides-info-box").contains(expected.features_description);
    });
  };

  const testTcfModalVendorsTabLocalization = (expected: TestTcfModalTranslations) => {
    cy.get("#fides-panel-Vendors").within(() => {
      cy.get(".fides-info-box").should("be.visible");
      cy.get(".fides-info-box").contains(expected.vendors_description);
      cy.get(".fides-radio-button-group button").then(buttons => {
        cy.wrap(buttons[0]).contains(expected.consent);
        cy.wrap(buttons[1]).contains(expected.legint);
      });
    });
  };

  const testTcfModalLocalization = (expected: TestTcfModalTranslations) => {
    // Start by opening the modal
    // NOTE: We could also use cy.get("#fides-modal-link").click(), but let's
    // assume the banner is visible in these tests
    cy.get("#fides-banner .fides-manage-preferences-button").click();
    cy.get("#fides-modal").should("be.visible");

    // Check modal localization
    cy.get("#fides-modal").within(() => {
      cy.get(".fides-modal-title").contains(expected.title);
      cy.get(".fides-modal-description").contains(expected.description);
      cy.get(".fides-modal-button-group").contains(expected.save_button_label);
      cy.get(".fides-modal-button-group").contains(
        expected.reject_button_label
      );
      cy.get(".fides-modal-button-group").contains(
        expected.accept_button_label
      );

      // Check each of the modal tabs
      cy.get(".fides-tabs .fides-tab-list li").then(items => {
        cy.wrap(items[0]).contains(expected.purposes).click();
        testTcfModalPurposesTabLocalization(expected);
        cy.wrap(items[1]).contains(expected.features).click();
        testTcfModalFeaturesTabLocalization(expected);
        cy.wrap(items[2]).contains(expected.vendors).click();
        testTcfModalVendorsTabLocalization(expected);
      });

      // Privacy policy link is optional; if provided, check that it is localized
      if (expected.privacy_policy_link_label) {
        cy.get("#fides-privacy-policy-link").contains(
          expected.privacy_policy_link_label
        );
        cy.get("#fides-privacy-policy-link a").should(
          "have.attr",
          "href",
          expected.privacy_policy_url
        );
      } else {
        cy.get("#fides-privacy-policy-link").should("not.exist");
      }
    });
  };
  describe("when auto_detect_language is true", () => {
    describe(`when browser language matches default locale (${ENGLISH_LOCALE})`, () => {
      it("localizes banner_and_modal components in the correct locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal.json",
        });
        // testBannerLocalization(ENGLISH_BANNER);
        openAndTestModalLocalization(ENGLISH_MODAL);
        testModalNoticesLocalization(ENGLISH_NOTICES);
      });

      it("handles optional translations for banner_and_modal components in the correct locale", () => {
        // Ensure that null/empty values for some optional translation messages provide their correct fallbacks
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal.json",
          overrideExperience: (experience: any) => {
            /* eslint-disable no-param-reassign */
            const translations = experience.experience_config.translations[0];
            translations.banner_description = null;
            translations.banner_title = "";
            translations.privacy_policy_link_label = null;
            translations.privacy_policy_url = null;
            return experience;
            /* eslint-enable no-param-reassign */
          },
        });

        testBannerLocalization({
          ...ENGLISH_BANNER,
          ...{
            // Expect banner to fallback to modal translations
            banner_title: ENGLISH_MODAL.title,
            banner_description: ENGLISH_MODAL.description,
            // Expect privacy policy link to not exist
            privacy_policy_link_label: null,
            privacy_policy_link_url: null,
          },
        });
        openAndTestModalLocalization({
          ...ENGLISH_MODAL,
          ...{
            // Expect privacy policy link to not exist
            privacy_policy_link_label: null,
            privacy_policy_link_url: null,
          },
        });
        testModalNoticesLocalization(ENGLISH_NOTICES);
      });

      it("localizes banner_and_modal notice-only components in the correct locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal_notice_only.json",
        });

        // Test notice-only banner
        cy.get("#fides-banner").within(() => {
          cy.get(".fides-banner-title").contains(ENGLISH_BANNER.banner_title);
          cy.get(".fides-banner-description").contains(
            ENGLISH_BANNER.banner_description
          );
          cy.get(".fides-acknowledge-button").contains(
            ENGLISH_BANNER.acknowledge_button_label
          );
        });

        // Test notice-only modal
        cy.get("#fides-modal-link").click();
        cy.get("#fides-modal").within(() => {
          cy.get(".fides-modal-title").contains(ENGLISH_MODAL.title);
          cy.get(".fides-modal-description").contains(
            ENGLISH_MODAL.description
          );
          cy.get(".fides-acknowledge-button").contains(
            ENGLISH_MODAL.acknowledge_button_label
          );
        });
      });

      it.skip("localizes modal components in the correct locale", () => {});

      it.only("localizes tcf_overlay components in the correct locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_tcf.json",
          options: { tcfEnabled: true },
        });

        testTcfBannerLocalization(ENGLISH_TCF_BANNER);
        testTcfModalLocalization(ENGLISH_TCF_MODAL);
      });

      it.skip("localizes privacy_center components in the correct locale", () => {});
    });

    describe(`when browser language matches an available locale (${SPANISH_LOCALE})`, () => {
      it("localizes banner_and_modal components in the correct locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: SPANISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal.json",
        });
        testBannerLocalization(SPANISH_BANNER);
        openAndTestModalLocalization(SPANISH_MODAL);
        testModalNoticesLocalization(SPANISH_NOTICES);
      });

      it("handles optional translations for banner_and_modal components in the correct locale", () => {
        // Ensure that null/empty values for some optional translation messages provide their correct fallbacks
        visitDemoWithI18n({
          navigatorLanguage: SPANISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal.json",
          overrideExperience: (experience: any) => {
            /* eslint-disable no-param-reassign */
            const translations = experience.experience_config.translations[1];
            translations.banner_description = null;
            translations.banner_title = "";
            translations.privacy_policy_link_label = null;
            translations.privacy_policy_url = null;
            return experience;
            /* eslint-enable no-param-reassign */
          },
        });

        testBannerLocalization({
          ...SPANISH_BANNER,
          ...{
            // Expect banner to fallback to modal translations
            banner_title: SPANISH_MODAL.title,
            banner_description: SPANISH_MODAL.description,
            // Expect privacy policy link to not exist
            privacy_policy_link_label: null,
            privacy_policy_link_url: null,
          },
        });
        openAndTestModalLocalization({
          ...SPANISH_MODAL,
          ...{
            // Expect privacy policy link to not exist
            privacy_policy_link_label: null,
            privacy_policy_link_url: null,
          },
        });
        testModalNoticesLocalization(SPANISH_NOTICES);
      });

      it("localizes banner_and_modal notice-only components in the correct locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: SPANISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal_notice_only.json",
        });

        // Test notice-only banner
        cy.get("#fides-banner").within(() => {
          cy.get(".fides-banner-title").contains(SPANISH_BANNER.banner_title);
          cy.get(".fides-banner-description").contains(
            SPANISH_BANNER.banner_description
          );
          cy.get(".fides-acknowledge-button").contains(
            SPANISH_BANNER.acknowledge_button_label
          );
        });

        // Test notice-only modal
        cy.get("#fides-modal-link").click();
        cy.get("#fides-modal").within(() => {
          cy.get(".fides-modal-title").contains(SPANISH_MODAL.title);
          cy.get(".fides-modal-description").contains(
            SPANISH_MODAL.description
          );
          cy.get(".fides-acknowledge-button").contains(
            SPANISH_MODAL.acknowledge_button_label
          );
        });
      });

      it.skip("localizes tcf_overlay components in the correct locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: SPANISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_tcf.json",
        });
        cy.window().its("navigator.language").should("eq", SPANISH_LOCALE);
      });

      it.skip("localizes privacy_center components in the correct locale", () => {});
    });

    describe(`when browser language does not match any available locale (${JAPANESE_LOCALE})`, () => {
      it("localizes banner_and_modal components in the correct locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: JAPANESE_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal.json",
        });
        testBannerLocalization(ENGLISH_BANNER);
        openAndTestModalLocalization(ENGLISH_MODAL);
        testModalNoticesLocalization(ENGLISH_NOTICES);
      });
    });
  });

  describe("when auto_detect_language is false", () => {
    it(`ignores browser locale and localizes in the default locale (${ENGLISH_LOCALE})`, () => {
      // Visit the demo site in Spanish, but expect English translations when auto-detection is disabled
      visitDemoWithI18n({
        navigatorLanguage: SPANISH_LOCALE,
        globalPrivacyControl: true,
        fixture: "experience_banner_modal.json",
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
  });

  describe(`when notices are missing translations that are available in the experience for the correct language (${SPANISH_LOCALE})`, () => {
    beforeEach(() => {
      // Visit the demo in Spanish, but remove all non-English translations from the Advertising notice
      visitDemoWithI18n({
        navigatorLanguage: SPANISH_LOCALE,
        globalPrivacyControl: true,
        fixture: "experience_banner_modal.json",
        overrideExperience: (experience: any) => {
          /* eslint-disable no-param-reassign */
          // Modify the first notice (Advertising) and delete all non-English translations
          const notices: PrivacyNotice[] = experience.privacy_notices;
          const adsNotice = notices[0];
          cy.wrap(adsNotice).should(
            "have.property",
            "id",
            "pri_notice-advertising-000"
          );
          adsNotice.has_gpc_flag = true;
          adsNotice.translations = adsNotice.translations.filter(
            (e) => e.language === "en"
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
        // NOTE: GPC preferences are saved before "notices served" could
        // possibly complete, so we expect this to be undefined
        expect(served_notice_history_id).to.eq(undefined);
        expect(privacy_experience_config_history_id).to.eq(
          "pri_exp-history-banner-modal-es-000"
        );
        const noticeHistoryIDs = preferences.map(
          (e: any) => e.privacy_notice_history_id
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
          "pri_exp-history-banner-modal-es-000"
        );
        expect(privacy_notice_history_ids).to.eql(EXPECTED_NOTICE_HISTORY_IDS);
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
        expect(served_notice_history_id).to.eq("ser_notice-history-000");
        expect(privacy_experience_config_history_id).to.eq(
          "pri_exp-history-banner-modal-es-000"
        );
        const noticeHistoryIDs = preferences.map(
          (e: any) => e.privacy_notice_history_id
        );
        expect(noticeHistoryIDs).to.eql(EXPECTED_NOTICE_HISTORY_IDS);
      });

      // TODO (PROD-1598): test that correct history ID used after user changes language
    });
    /* eslint-enable @typescript-eslint/naming-convention */
  });

  describe("when notices are enabled for GPC", () => {
    it(`localizes GPC badges on notices in the correct locale (${SPANISH_LOCALE})`, () => {
      // Visit the demo in Spanish and set GPC flag on the first notice
      visitDemoWithI18n({
        navigatorLanguage: SPANISH_LOCALE,
        globalPrivacyControl: true,
        fixture: "experience_banner_modal.json",
        overrideExperience: (experience: any) => {
          /* eslint-disable no-param-reassign */
          // Modify the first notice (Advertising) to set the GPC flag
          const notices: PrivacyNotice[] = experience.privacy_notices;
          const adsNotice = notices[0];
          cy.wrap(adsNotice).should(
            "have.property",
            "id",
            "pri_notice-advertising-000"
          );
          adsNotice.has_gpc_flag = true;
          return experience;
          /* eslint-enable no-param-reassign */
        },
      });

      // Open the modal and check the notices themselves are translated
      testBannerLocalization(SPANISH_BANNER);
      openAndTestModalLocalization(SPANISH_MODAL);
      testModalNoticesLocalization(SPANISH_NOTICES);

      // Check the GPC badge labels on the first notice
      const expectedGpcLabel = SPANISH_BANNER.gpc_label;
      const expectedGpcStatusAppliedLabel = "Aplicado";
      const expectedGpcStatusOverriddenLabel = "Anulado";
      cy.get(
        "#fides-modal .fides-modal-notices .fides-notice-toggle:first"
      ).within(() => {
        cy.get(".fides-notice-toggle-title").contains(SPANISH_NOTICES[0].title);
        cy.get(".fides-gpc-label").contains(expectedGpcLabel);
        cy.get(".fides-gpc-label .fides-gpc-badge").contains(
          expectedGpcStatusAppliedLabel
        );
        cy.get(".fides-toggle-input").click();
        cy.get(".fides-gpc-label .fides-gpc-badge").contains(
          expectedGpcStatusOverriddenLabel
        );
      });
      cy.get(
        "#fides-modal .fides-modal-notices .fides-notice-toggle:last"
      ).within(() => {
        cy.get(".fides-gpc-label").should("not.exist");
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
      testBannerLocalization(SPANISH_BANNER);
      openAndTestModalLocalization(SPANISH_MODAL);
      testModalNoticesLocalization(SPANISH_NOTICES);
    });
  });

  describe("when localizing the 'On'/'Off' toggle labels", () => {
    describe(`when in the default locale (${ENGLISH_LOCALE})`, () => {
      it("shows the 'On'/'Off' toggle labels in banner_and_modal components", () => {
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

      it("shows the 'On'/'Off' toggle labels in tcf_overlay components", () => {
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          fixture: "experience_tcf.json",
          options: { tcfEnabled: true },
        });
        cy.get("#fides-modal-link").click();
        cy.getByTestId("records-list-Purposes").within(() => {
          cy.get(".fides-toggle:first").contains("Off");
          cy.get(".fides-toggle:first").click();
          cy.get(".fides-toggle:first").contains("On");
        });
      });
    });

    describe(`when in any non-default locale (${SPANISH_LOCALE})`, () => {
      it("hides the 'On'/'Off' toggle labels in banner_and_modal components", () => {
        visitDemoWithI18n({
          navigatorLanguage: SPANISH_LOCALE,
          fixture: "experience_banner_modal.json",
        });
        cy.get("#fides-modal-link").click();
        cy.get("#fides-modal .fides-modal-notices").within(() => {
          cy.get(".fides-toggle:first").contains("Off").should("not.exist");
          cy.get(".fides-toggle:first .fides-toggle-display").should(
            "be.empty"
          );
          cy.get(".fides-toggle:first").click();
          cy.get(".fides-toggle:first").contains("On").should("not.exist");
          cy.get(".fides-toggle:first .fides-toggle-display").should(
            "be.empty"
          );
        });
      });

      it("hides the 'On'/'Off' toggle labels in tcf_overlay components", () => {
        visitDemoWithI18n({
          navigatorLanguage: SPANISH_LOCALE,
          fixture: "experience_tcf.json",
          options: { tcfEnabled: true },
        });
        cy.get("#fides-modal-link").click();
        cy.getByTestId("records-list-Purposes").within(() => {
          cy.get(".fides-toggle:first").contains("Off").should("not.exist");
          cy.get(".fides-toggle:first .fides-toggle-display").should(
            "be.empty"
          );
          cy.get(".fides-toggle:first").click();
          cy.get(".fides-toggle:first").contains("On").should("not.exist");
          cy.get(".fides-toggle:first .fides-toggle-display").should(
            "be.empty"
          );
        });
      });
    });
  });

  // TODO (PROD-1598): enable this test and add other cases as needed!
  describe.skip("when user selects their own locale", () => {
    it(`localizes in the user selected locale (${SPANISH_LOCALE})`, () => {
      // Visit the demo site in English, but expect Spanish translations when the user selects
      visitDemoWithI18n({
        navigatorLanguage: ENGLISH_LOCALE,
        globalPrivacyControl: true,
        fixture: "experience_banner_modal.json",
      });
      // TODO (PROD-1598): select Spanish from banner
      testBannerLocalization(SPANISH_BANNER);
      openAndTestModalLocalization(SPANISH_MODAL);
      testModalNoticesLocalization(SPANISH_NOTICES);
    });
  });
});
