import {
  CONSENT_COOKIE_NAME,
  FidesConfig,
  FidesCookie,
  ConsentMechanism,
  EnforcementLevel,
  ExperienceComponent,
  ExperienceDeliveryMechanism,
} from "fides-js";

const PRIVACY_NOTICE_ID_1 = "pri_4bed96d0-b9e3-4596-a807-26b783836374";
const PRIVACY_NOTICE_ID_2 = "pri_4bed96d0-b9e3-4596-a807-26b783836375";

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
        {
          name: "Essential",
          description:
            "Notify the user about data processing activities that are essential to your services functionality. Typically consent is not required for this.",
          regions: ["us_ca"],
          consent_mechanism: ConsentMechanism.NOTICE_ONLY,
          has_gpc_flag: true,
          data_uses: ["provide.service"],
          enforcement_level: EnforcementLevel.SYSTEM_WIDE,
          displayed_in_overlay: true,
          displayed_in_api: true,
          displayed_in_privacy_center: false,
          id: "pri_4bed96d0-b9e3-4596-a807-26b783836375",
          created_at: "2023-04-24T21:29:08.870351+00:00",
          updated_at: "2023-04-24T21:29:08.870351+00:00",
          version: 1.0,
          privacy_notice_history_id: "pri_b09058a7-9f54-4360-8da5-4521e8975d4e",
        },
      ],
    },
    geolocation: {},
    options: {
      debug: true,
      isOverlayDisabled: false,
      isGeolocationEnabled: false,
      geolocationApiUrl: "",
      privacyCenterUrl: "http://localhost:3000",
    },
  };

  describe("when disabled", () => {
    beforeEach(() => {
      // todo- need a better test pattern for overriding default config
      const newTestOptions = testBannerOptions;
      newTestOptions.options.isOverlayDisabled = true;
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
        newTestOptions.options.isOverlayDisabled = false;
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
              "button#fides-consent-banner-button-secondary.fides-consent-banner-button.fides-consent-banner-button-secondary"
            ).contains("Manage preferences");
            cy.get(
              "button#fides-consent-banner-button-primary.fides-consent-banner-button.fides-consent-banner-button-primary"
            ).contains("Reject Test");
            cy.get(
              "button#fides-consent-banner-button-primary.fides-consent-banner-button.fides-consent-banner-button-primary"
            ).contains("Accept Test");
            // Order matters - it should always be secondary, then primary!
            cy.get("button")
              .eq(0)
              .should("have.id", "fides-consent-banner-button-secondary");
            cy.get("button")
              .eq(1)
              .should("have.id", "fides-consent-banner-button-primary");
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
              .property(PRIVACY_NOTICE_ID_1)
              .is.eql(true);
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_ID_2)
              .is.eql(true);
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
              .property(PRIVACY_NOTICE_ID_1)
              .is.eql(false);
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_ID_2)
              .is.eql(false);
          });
        });
      });

      describe("modal", () => {
        it("should open modal when experience component = OVERLAY", () => {
          cy.contains("button", "Manage preferences").click();
          cy.getByTestId("consent-modal");
        });

        it("can toggle the notices", () => {
          cy.contains("button", "Manage preferences").click();
          // Notices should start off disabled
          cy.getByTestId("toggle-Test privacy notice").within(() => {
            cy.get("input").should("not.have.attr", "checked");
          });
          cy.getByTestId("toggle-Test privacy notice").click();
          cy.getByTestId("toggle-Essential").within(() => {
            cy.get("input").should("not.have.attr", "checked");
          });
          cy.getByTestId("toggle-Essential").click();

          // DEFER: intercept and check the API call once it is hooked up
          cy.getByTestId("Save-btn").click();
          // Modal should close after saving
          cy.getByTestId("consent-modal").should("not.exist");

          // check that the cookie updated
          cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value)
              );
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_ID_1)
                .is.eql(true);
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_ID_2)
                .is.eql(true);
            });
          });

          // check that window.Fides.consent updated
          cy.window().then((win) => {
            expect(win.Fides.consent).to.eql({
              [PRIVACY_NOTICE_ID_1]: true,
              [PRIVACY_NOTICE_ID_2]: true,
            });
          });

          // Upon reload, window.Fides should make the notices enabled
          cy.reload();
          cy.contains("button", "Manage preferences").click();
          cy.getByTestId("toggle-Test privacy notice").within(() => {
            cy.get("input").should("have.attr", "checked");
          });
          cy.getByTestId("toggle-Essential").within(() => {
            cy.get("input").should("have.attr", "checked");
          });
        });
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
