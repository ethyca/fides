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

  describe("when auto_detect_language is true", () => {
    describe(`when browser language matches default locale (${ENGLISH_LOCALE})`, () => {
      it("localizes banner_and_modal components in the correct locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_banner_modal.json",
        });
        testBannerLocalization(ENGLISH_BANNER);
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

      it.skip("localizes tcf_overlay components in the correct locale", () => {
        visitDemoWithI18n({
          navigatorLanguage: ENGLISH_LOCALE,
          globalPrivacyControl: true,
          fixture: "experience_tcf.json",
        });
        cy.window().its("navigator.language").should("eq", ENGLISH_LOCALE);
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
        const { method, served_notice_history_id, privacy_experience_config_history_id, preferences } =
          interception.request.body;
        expect(method).to.eq("gpc");
        // NOTE: GPC preferences are saved before "notices served" could
        // possibly complete, so we expect this to be undefined
        expect(served_notice_history_id).to.be.undefined;
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
        const { method, served_notice_history_id, privacy_experience_config_history_id, preferences } =
          interception.request.body;
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
