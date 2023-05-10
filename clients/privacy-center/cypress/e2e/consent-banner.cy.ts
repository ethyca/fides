import {
  CONSENT_COOKIE_NAME,
  FidesConfig,
  FidesCookie,
  ConsentMechanism,
  EnforcementLevel,
  ExperienceComponent,
  ExperienceDeliveryMechanism,
} from "fides-js";

// The fides-js-components-demo.html page is wired up to inject the
// `fidesConfig` into the Fides.init(...) function
declare global {
  interface Window {
    fidesConfig?: FidesConfig;
  }
}

// We define a custom Cypress command
declare global {
  namespace Cypress {
    interface Chainable {
      visitConsentDemo(options?: FidesConfig): Chainable<any>;
    }
  }
}

describe("Consent banner", () => {
  // Default options to use for all tests
  const testBannerOptions: FidesConfig = {
    consent: {
      options: [
        {
          cookieKeys: ["data_sales"],
          default: true,
          fidesDataUseKey: "data_use.sales",
        },
        {
          cookieKeys: ["tracking"],
          default: false,
          fidesDataUseKey: "advertising",
        },
      ],
    },
    experience: {
      version: "1.0",
      component: ExperienceComponent.OVERLAY,
      delivery_mechanism: ExperienceDeliveryMechanism.BANNER,
      regions: ["us_ca", "us_co"],
      component_title: "Manage your consent",
      component_description:
        "On this page you can opt in and out of these data uses cases",
      banner_title: "Manage your consent",
      banner_description:
        "This test website is overriding the banner description label.",
      confirmation_button_label: "Accept Test",
      reject_button_label: "Reject Test",
      privacy_notices: [
        {
          name: "Test privacy notice",
          description: "a test sample privacy notice configuration",
          regions: ["us_ca"],
          consent_mechanism: ConsentMechanism.OPT_IN,
          has_gpc_flag: true,
          data_uses: ["advertising", "third_party_sharing"],
          enforcement_level: EnforcementLevel.SYSTEM_WIDE,
          displayed_in_overlay: true,
          displayed_in_api: true,
          displayed_in_privacy_center: false,
          id: "pri_4bed96d0-b9e3-4596-a807-26b783836374",
          created_at: "2023-04-24T21:29:08.870351+00:00",
          updated_at: "2023-04-24T21:29:08.870351+00:00",
          version: 1.0,
          privacy_notice_history_id: "pri_b09058a7-9f54-4360-8da5-4521e8975d4f",
        },
      ],
    },
    geolocation: {},
    options: {
      debug: true,
      isDisabled: false,
      isGeolocationEnabled: false,
      geolocationApiUrl: "",
      privacyCenterUrl: "http://localhost:3000",
    },
  };

  Cypress.Commands.add("visitConsentDemo", (options?: FidesConfig) => {
    cy.visit("/fides-js-components-demo.html", {
      onBeforeLoad: (win) => {
        // eslint-disable-next-line no-param-reassign
        win.fidesConfig = options;
      },
    });
  });

  describe("when disabled", () => {
    beforeEach(() => {
      // todo- need a better test pattern for overriding default config
      const newTestOptions = testBannerOptions;
      newTestOptions.options.isDisabled = true;
      cy.visitConsentDemo(newTestOptions);
    });

    it("does not render", () => {
      cy.get("div#fides-consent-banner").should("not.exist");
      cy.contains("button", "Accept Test").should("not.exist");
    });
  });

  describe("when user has no saved consent cookie", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    });

    describe("when banner is not disabled", () => {
      beforeEach(() => {
        const newTestOptions = testBannerOptions;
        newTestOptions.options.isDisabled = false;
        newTestOptions.options.isGeolocationEnabled = false;
        cy.visitConsentDemo(newTestOptions);
      });

      it("should render the expected HTML banner", () => {
        cy.get("div#fides-consent-banner.fides-consent-banner").within(() => {
          cy.get(
            "div#fides-consent-banner-description.fides-consent-banner-description"
          ).contains(
            "This test website is overriding the banner description label."
          );
          cy.get(
            "div#fides-consent-banner-buttons.fides-consent-banner-buttons"
          ).within(() => {
            cy.get(
              "button#fides-consent-banner-button-tertiary.fides-consent-banner-button.fides-consent-banner-button-tertiary"
            ).contains("Manage Preferences");
            cy.get(
              "button#fides-consent-banner-button-secondary.fides-consent-banner-button.fides-consent-banner-button-secondary"
            ).contains("Reject Test");
            cy.get(
              "button#fides-consent-banner-button-primary.fides-consent-banner-button.fides-consent-banner-button-primary"
            ).contains("Accept Test");
            // Order matters - it should always be tertiary, then secondary, then primary!
            cy.get("button")
              .eq(0)
              .should("have.id", "fides-consent-banner-button-tertiary");
            cy.get("button")
              .eq(1)
              .should("have.id", "fides-consent-banner-button-secondary");
            cy.get("button")
              .eq(2)
              .should("have.id", "fides-consent-banner-button-primary");
          });
        });
      });

      it("should allow accepting all", () => {
        cy.contains("button", "Accept Test").should("be.visible").click();
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value)
            );
            expect(cookieKeyConsent.consent)
              .property("data_sales")
              .is.eql(true);
            expect(cookieKeyConsent.consent).property("tracking").is.eql(true);
          });
          cy.contains("button", "Accept Test").should("not.be.visible");
        });
      });

      it("should support rejecting all consent options", () => {
        cy.contains("button", "Reject Test").should("be.visible").click();
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value)
            );
            expect(cookieKeyConsent.consent)
              .property("data_sales")
              .is.eql(false);
            expect(cookieKeyConsent.consent).property("tracking").is.eql(false);
          });
        });
      });

      it("should navigate to Privacy Center to manage consent options", () => {
        cy.contains("button", "Manage Preferences")
          .should("be.visible")
          .click();
        cy.url().should("equal", "http://localhost:3000/");
      });

      it.skip("should save the consent request to the Fides API", () => {
        // TODO: add tests for saving to API (ie PATCH /api/v1/consent-request/{id}/preferences...)
        expect(false).is.eql(true);
      });

      it.skip("should support option to display at top or bottom of page", () => {
        // TODO: add tests for top/bottom
        expect(false).is.eql(true);
      });

      it.skip("should support styling with CSS variables", () => {
        // TODO: add tests for CSS
        expect(false).is.eql(true);
      });
    });
  });
});
