import { FidesOptions } from "fides-js";
import { stubConfig } from "../support/stubs";

describe("Consent i18n", () => {
  const ENGLISH_LOCALE = "en-US";
  const SPANISH_LOCALE = "es-ES";
  const JAPANESE_LOCALE = "ja-JP";
  type TestFixture =
    | "experience_banner_modal.json"
    | "experience_tcf.json"
    | "experience_privacy_center.json";

  // Setup a test case with the given params
  const visitDemoWithI18n = (
    navigatorLanguage: string,
    fixture: TestFixture,
    options?: Partial<FidesOptions>
  ) => {
    cy.on("window:before:load", (win) => {
      // eslint-disable-next-line no-param-reassign
      Object.defineProperty(win.navigator, "language", {
        value: navigatorLanguage,
      });
    });
    cy.fixture(`consent/${fixture}`).then((data) => {
      const experience = data.items[0];
      cy.log(`Using PrivacyExperience data from ${fixture}`, experience);
      stubConfig({ experience, options });
    });
    cy.window().its("navigator.language").should("eq", navigatorLanguage);
  };

  // Reusable assertions to test that the banner component localizes correctly
  const testBannerLocalization = (expected: {
    banner_title: string;
    banner_description: string;
    privacy_preferences_link_label: string;
    reject_button_label: string;
    accept_button_label: string;
    privacy_policy_link_label: string;
    privacy_policy_url: string;
  }) => {
    // Check banner localization
    cy.get("#fides-banner").within(() => {
      cy.get(".fides-banner-title").contains(expected.banner_title);
      cy.get(".fides-banner-description").contains(expected.banner_description);
      cy.get("#fides-button-group").contains(
        expected.privacy_preferences_link_label
      );
      cy.get("#fides-button-group").contains(expected.reject_button_label);
      cy.get("#fides-button-group").contains(expected.accept_button_label);
      // TODO: re-enable
      // cy.get("#fides-privacy-policy-link").contains(translation.privacy_policy_link_label);
      // cy.get("#fides-privacy-policy-link").should("have.attr", "href", translation.privacy_policy_url);

      // untested
      // "acknowledge_button_label": "OK",
    });
  };

  // Reusable assertions to test that the modal component localizes correctly
  const testModalLocalization = (expected: {
    title: string;
    description: string;
    save_button_label: string;
    reject_button_label: string;
    accept_button_label: string;
    privacy_policy_link_label: string;
    privacy_policy_url: string;
  }) => {
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
      // TODO: re-enable
      // cy.get("#fides-privacy-policy-link").contains(translation.privacy_policy_link_label);
      // cy.get("#fides-privacy-policy-link").should("have.attr", "href", translation.privacy_policy_url);
    });
  };

  // Reusable assertions to test that the modal notices component localizes correctly
  const testModalNoticesLocalization = (
    expected: {
      title: string;
      description: string;
    }[]
  ) => {
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
        visitDemoWithI18n(ENGLISH_LOCALE, "experience_banner_modal.json");

        testBannerLocalization({
          banner_title: "[banner] Manage your consent preferences",
          banner_description: "[banner] We use cookies and similar",
          privacy_preferences_link_label: "Manage preferences",
          reject_button_label: "Opt out of all",
          accept_button_label: "Opt in to all",
          privacy_policy_link_label: "Privacy Policy",
          privacy_policy_url: "https://privacy.example.com/",
        });

        cy.get("#fides-banner #fides-button-group")
          .contains("Manage preferences")
          .click();
        testModalLocalization({
          title: "Manage your consent preferences",
          description: "We use cookies and similar",
          save_button_label: "Save",
          reject_button_label: "Opt out of all",
          accept_button_label: "Opt in to all",
          privacy_policy_link_label: "Privacy Policy",
          privacy_policy_url: "https://privacy.example.com/",
        });

        // Check modal notices localization
        testModalNoticesLocalization([
          { title: "Advertising", description: "This website uses marketing" },
          { title: "Analytics", description: "This website uses analytics" },
          { title: "Essential", description: "This website uses essential" },
        ]);
      });

      it.skip("localizes tcf_overlay components in the correct locale", () => {
        visitDemoWithI18n(ENGLISH_LOCALE, "experience_tcf.json");
        cy.window().its("navigator.language").should("eq", ENGLISH_LOCALE);
      });

      it.skip("localizes privacy_center components in the correct locale", () => {});
    });

    describe(`when browser language matches an available locale (${SPANISH_LOCALE})`, () => {
      it("localizes banner_and_modal components in the correct locale", () => {
        visitDemoWithI18n(SPANISH_LOCALE, "experience_banner_modal.json");
        cy.window().its("navigator.language").should("eq", SPANISH_LOCALE);
      });

      it.skip("localizes tcf_overlay components in the correct locale", () => {
        visitDemoWithI18n(SPANISH_LOCALE, "experience_tcf.json");
        cy.window().its("navigator.language").should("eq", SPANISH_LOCALE);
      });

      it.skip("localizes privacy_center components in the correct locale", () => {});
    });

    describe(`when browser language does not match any available locale (${JAPANESE_LOCALE})`, () => {
      it("localizes banner_and_modal components in the correct locale", () => {
        visitDemoWithI18n(JAPANESE_LOCALE, "experience_banner_modal.json");
        cy.window().its("navigator.language").should("eq", JAPANESE_LOCALE);
      });

      it.skip("localizes tcf_overlay components in the correct locale", () => {
        visitDemoWithI18n(JAPANESE_LOCALE, "experience_tcf.json");
        cy.window().its("navigator.language").should("eq", JAPANESE_LOCALE);
      });

      it.skip("localizes privacy_center components in the correct locale", () => {});
    });
  });

  describe.skip("when auto_detect_language is false", () => {
    it(`always localizes in the default locale (${ENGLISH_LOCALE})`, () => {
      // visit in spanish, expect english
    });
  });

  describe.skip("when user selects their own language", () => {
    it("renders...", () => {});
    it("does not allow renders...", () => {});
  });

  it("should render the banner", () => {});
});
