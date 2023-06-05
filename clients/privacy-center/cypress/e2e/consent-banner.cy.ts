import {
  CONSENT_COOKIE_NAME,
  ComponentType,
  DeliveryMechanism,
  FidesCookie,
} from "fides-js";
import {
  FidesOptions,
  PrivacyExperience,
  UserGeolocation,
} from "fides-js/src/lib/consent-types";
import { ConsentConfig } from "fides-js/src/lib/consent-config";

enum OVERRIDE {
  // signals that we should override entire prop with undefined
  EMPTY = "Empty",
}

export interface FidesConfigTesting {
  // We don't need all required props to override the default config
  consent?: Partial<ConsentConfig> | OVERRIDE;
  experience?: Partial<PrivacyExperience> | OVERRIDE;
  geolocation?: Partial<UserGeolocation> | OVERRIDE;
  options: Partial<FidesOptions> | OVERRIDE;
}

/**
 * Helper function to swap out config
 * @example stubExperience({experience: {component: ComponentType.PRIVACY_CENTER}})
 */
const stubConfig = ({
  consent,
  experience,
  geolocation,
  options,
}: Partial<FidesConfigTesting>) => {
  cy.fixture("consent/test_banner_options.json").then((config) => {
    const updatedConfig = {
      consent:
        consent === OVERRIDE.EMPTY
          ? undefined
          : Object.assign(config.consent, consent),
      experience:
        experience === OVERRIDE.EMPTY
          ? undefined
          : Object.assign(config.experience, experience),
      geolocation:
        geolocation === OVERRIDE.EMPTY
          ? undefined
          : Object.assign(config.geolocation, geolocation),
      options:
        options === OVERRIDE.EMPTY
          ? undefined
          : Object.assign(config.options, options),
    };
    if (typeof options !== "string" && options?.geolocationApiUrl) {
      cy.intercept("GET", options.geolocationApiUrl, {
        body: {
          country: "US",
          ip: "63.173.339.012:13489",
          location: "US-CA",
          region: "CA",
        },
      }).as("getGeolocation");
    }
    cy.visitConsentDemo(updatedConfig);
  });
};

const PRIVACY_NOTICE_ID_1 = "pri_4bed96d0-b9e3-4596-a807-26b783836374";
const PRIVACY_NOTICE_ID_2 = "pri_4bed96d0-b9e3-4596-a807-26b783836375";

describe("Consent banner", () => {
  describe("when overlay is disabled", () => {
    beforeEach(() => {
      stubConfig({
        options: {
          isOverlayDisabled: true,
        },
      });
    });

    it("does not render banner", () => {
      cy.get("div#fides-consent-banner").should("not.exist");
      cy.contains("button", "Accept Test").should("not.exist");
    });
    it("does not render modal link", () => {
      cy.get("#fides-consent-modal-link").should("not.be.visible");
    });
  });

  describe("when user has no saved consent cookie", () => {
    describe("when banner is not disabled", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          options: {
            isOverlayDisabled: false,
          },
        });
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
      it("does not render modal link", () => {
        cy.get("#fides-consent-modal-link").should("not.be.visible");
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

      it("overwrites privacy notices that no longer exist", () => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const now = "2023-04-28T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: { version: "0.9.0", createdAt: now },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));
        cy.contains("button", "Manage preferences").click();

        // Save new preferences
        cy.getByTestId("toggle-Test privacy notice").click();
        cy.getByTestId("toggle-Essential").click();
        cy.getByTestId("Save-btn").click();

        // New privacy notice values only, no legacy ones
        const expectedConsent = {
          [PRIVACY_NOTICE_ID_1]: true,
          [PRIVACY_NOTICE_ID_2]: true,
        };
        // check that the cookie updated
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value)
            );
            expect(cookieKeyConsent.consent).eql(expectedConsent);
          });
        });

        // check that window.Fides.consent updated
        cy.window().then((win) => {
          expect(win.Fides.consent).to.eql(expectedConsent);
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

    describe("when GPC flag is found, and notices apply to GPC", () => {
      it.skip("sends GPC consent override downstream to Fides API", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      });

      it.skip("stores consent in cookie", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      });
    });
    describe("when GPC flag is found, and no notices apply to GPC", () => {
      it.skip("does not send GPC consent override downstream to Fides API", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      });

      it.skip("does not store consent in cookie", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      });
    });
    describe("when no GPC flag is found, and notices apply to GPC", () => {
      it.skip("does not send GPC consent override downstream to Fides API", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      });

      it.skip("does not store consent in cookie", () => {
        // TODO: add tests for GPC
        expect(false).is.eql(true);
      });
    });
    describe("when experience component is not an overlay", () => {
      beforeEach(() => {
        stubConfig({
          experience: {
            component: ComponentType.PRIVACY_CENTER,
          },
        });
      });

      it("does not render banner", () => {
        cy.get("div#fides-consent-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });
      it("does not render modal link", () => {
        cy.get("#fides-consent-modal-link").should("not.be.visible");
      });
    });

    describe("when experience is not provided, and valid geolocation is provided", () => {
      beforeEach(() => {
        stubConfig({
          experience: OVERRIDE.EMPTY,
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
        });
      });

      it.skip("renders the banner", () => {
        // TODO: add when we are able to retrieve experience via API from fides.js
        expect(false).is.eql(true);
      });
      it("does not render modal link", () => {
        cy.get("#fides-consent-modal-link").should("not.be.visible");
      });
    });

    describe("when neither experience nor geolocation is provided, but geolocationApiUrl is defined", () => {
      describe("when geolocation is successful", () => {
        beforeEach(() => {
          const geoLocationUrl = "https://some-geolocation-api.com";
          stubConfig({
            experience: OVERRIDE.EMPTY,
            geolocation: OVERRIDE.EMPTY,
            options: {
              isGeolocationEnabled: true,
              geolocationApiUrl: geoLocationUrl,
            },
          });
        });

        it("renders the banner", () => {
          cy.wait("@getGeolocation");
          // TODO: add assertion for fetching experience
          // TODO: add assertion for rendering banner
        });
        it.skip("hides the modal link", () => {
          // TODO: add when we have link binding working
          expect(false).is.eql(true);
        });
      });

      describe("when geolocation is not successful", () => {
        beforeEach(() => {
          const geoLocationUrl = "https://some-geolocation-api.com";
          // mock failed geolocation api call
          cy.intercept("GET", geoLocationUrl, {
            body: undefined,
          }).as("getGeolocation");
          stubConfig({
            experience: OVERRIDE.EMPTY,
            geolocation: OVERRIDE.EMPTY,
            options: {
              isGeolocationEnabled: true,
              geolocationApiUrl: geoLocationUrl,
            },
          });
        });
        it.skip("does not render", () => {
          cy.wait("@getGeolocation");
          // TODO: add assertion for fetching experience
          // TODO: add assertion for banner not rendering after we implement experience api call
        });
        it.skip("hides the modal link", () => {
          // TODO: add when we have link binding working
          expect(false).is.eql(true);
        });
      });
    });

    // TODO: it should be possible in the future to filter for experience on just country
    describe("when experience is not provided, and geolocation is invalid", () => {
      beforeEach(() => {
        stubConfig({
          experience: OVERRIDE.EMPTY,
          geolocation: {
            country: "US",
          },
          options: {
            isGeolocationEnabled: true,
            geolocationApiUrl: "https://some-geolocation-api.com",
          },
        });
      });

      it("fetches geolocation from API and renders the banner", () => {
        cy.wait("@getGeolocation");
        // todo: add banner render assertion when we have experience API call
      });

      it("does not render modal link", () => {
        cy.get("#fides-consent-modal-link").should("not.be.visible");
      });
    });

    describe("when experience is not provided, and geolocation is not provided, but geolocation is disabled", () => {
      beforeEach(() => {
        stubConfig({
          experience: OVERRIDE.EMPTY,
          geolocation: OVERRIDE.EMPTY,
          options: {
            isGeolocationEnabled: false,
          },
        });
      });

      it("does not render banner", () => {
        cy.get("div#fides-consent-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });

      it("does not render modal link", () => {
        cy.get("#fides-consent-modal-link").should("not.be.visible");
      });
    });

    describe("when experience contains no notices", () => {
      beforeEach(() => {
        stubConfig({
          experience: {
            privacy_notices: [],
          },
        });
      });

      it("does not render banner", () => {
        cy.get("div#fides-consent-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });

      it("does not render modal link", () => {
        cy.get("#fides-consent-modal-link").should("not.be.visible");
      });
    });

    describe("when experience delivery mechanism is link", () => {
      beforeEach(() => {
        stubConfig({
          experience: {
            delivery_mechanism: DeliveryMechanism.LINK,
          },
        });
      });

      it("does not render banner", () => {
        cy.get("div#fides-consent-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });

      it("shows the modal link", () => {
        cy.get("#fides-consent-modal-link").should("be.visible");
      });

      describe("modal link click", () => {
        it.skip("should open modal", () => {
          // TODO: add when we have link binding working
          expect(false).is.eql(true);
        });
      });
    });
  });
});
