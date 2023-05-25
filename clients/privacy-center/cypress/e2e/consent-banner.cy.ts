import LegacyConsentConfig, {
  ComponentType,
  CONSENT_COOKIE_NAME,
  ConsentMethod,
  DeliveryMechanism,
  FidesCookie,
} from "fides-js";
import {
  ConsentMechanism,
  EnforcementLevel,
  FidesOptions,
  PrivacyExperience,
  UserConsentPreference,
  UserGeolocation,
} from "fides-js/src/lib/consent-types";
import { FidesEndpointPaths } from "fides-js/src/services/fides/api";

enum OVERRIDE {
  // signals that we should override entire prop with undefined
  EMPTY = "Empty",
}

export interface FidesConfigTesting {
  // We don't need all required props to override the default config
  consent?: Partial<LegacyConsentConfig> | OVERRIDE;
  experience?: Partial<PrivacyExperience> | OVERRIDE;
  geolocation?: Partial<UserGeolocation> | OVERRIDE;
  options: Partial<FidesOptions> | OVERRIDE;
}

/**
 * Helper function to swap out config
 * @example stubExperience({experience: {component: ComponentType.PRIVACY_CENTER}})
 */
const stubConfig = (
  { consent, experience, geolocation, options }: Partial<FidesConfigTesting>,
  mockGeolocationApiResp?: any
) => {
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
    if (
      typeof updatedConfig.options !== "string" &&
      updatedConfig.options?.geolocationApiUrl
    ) {
      const geoLocationResp = mockGeolocationApiResp || {
        body: {
          country: "US",
          ip: "63.173.339.012:13489",
          location: "US-CA",
          region: "CA",
        },
      };
      cy.intercept(
        "GET",
        updatedConfig.options.geolocationApiUrl,
        geoLocationResp
      ).as("getGeolocation");
    }
    if (
      typeof updatedConfig.options !== "string" &&
      updatedConfig.options?.fidesApiUrl
    ) {
      cy.intercept(
        "GET",
        `${updatedConfig.options.fidesApiUrl}${FidesEndpointPaths.PRIVACY_EXPERIENCE}*`,
        {
          fixture: "consent/privacy-experience.json",
        }
      ).as("getPrivacyExperience");
      cy.intercept(
        "PATCH",
        `${updatedConfig.options.fidesApiUrl}${FidesEndpointPaths.PRIVACY_PREFERENCES}`,
        {
          body: {},
        }
      ).as("patchPrivacyPreference");
    }
    cy.visitConsentDemo(updatedConfig);
  });
};

const PRIVACY_NOTICE_KEY_1 = "advertising";
const PRIVACY_NOTICE_KEY_2 = "essential";

describe("Consent banner", () => {
  describe("when overlay is disabled", () => {
    describe("when both experience and legacy consent exist", () => {
      beforeEach(() => {
        stubConfig({
          options: {
            isOverlayDisabled: true,
          },
        });
      });
      it("sets Fides.consent object with default consent based on privacy notices", () => {
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: false,
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
    describe("when only legacy consent exists", () => {
      beforeEach(() => {
        stubConfig({
          options: {
            isOverlayDisabled: true,
          },
          experience: OVERRIDE.EMPTY,
        });
      });
      it("sets Fides.consent object with default consent based on legacy consent", () => {
        cy.window().its("Fides").its("consent").should("eql", {
          data_sales: true,
          tracking: false,
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
              .property(PRIVACY_NOTICE_KEY_1)
              .is.eql(true);
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_2)
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
              .property(PRIVACY_NOTICE_KEY_1)
              .is.eql(false);
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_2)
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

          cy.getByTestId("Save-btn").click();
          // Modal should close after saving
          cy.getByTestId("consent-modal").should("not.exist");

          // check that consent was sent to Fides API
          let generatedUserDeviceId: string;
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            const expected = {
              // browser_identity.fides_user_device_id is intentionally left out here
              // so we can later assert to be any string
              preferences: [
                {
                  privacy_notice_history_id:
                    "pri_b09058a7-9f54-4360-8da5-4521e8975d4f",
                  preference: "opt_in",
                },
                {
                  privacy_notice_history_id:
                    "pri_b09058a7-9f54-4360-8da5-4521e8975d4e",
                  preference: "acknowledge",
                },
              ],
              privacy_experience_history_id: "2342345",
              user_geography: "us_ca",
              method: ConsentMethod.button,
            };
            // uuid is generated automatically if the user has no saved consent cookie
            generatedUserDeviceId = body.browser_identity.fides_user_device_id;
            expect(generatedUserDeviceId).to.be.a("string");
            expect(body.preferences).to.eql(expected.preferences);
            expect(body.privacy_experience_history_id).to.eql(
              expected.privacy_experience_history_id
            );
            expect(body.user_geography).to.eql(expected.user_geography);
            expect(body.method).to.eql(expected.method);
          });

          // check that the cookie updated
          cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value)
              );
              expect(cookieKeyConsent.identity.fides_user_device_id).is.eql(
                generatedUserDeviceId
              );
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_1)
                .is.eql(true);
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_2)
                .is.eql(true);
            });
          });

          // check that window.Fides.consent updated
          cy.window()
            .its("Fides")
            .its("consent")
            .should("eql", {
              [PRIVACY_NOTICE_KEY_1]: true,
              [PRIVACY_NOTICE_KEY_2]: true,
            });

          // Upon reload, window.Fides should make the notices enabled
          // Note that this doesn't replicate real world, in which a true reload would re-fetch
          // experience from the API, and those experience would likely not have net new notices
          // that require consent. In that case the banner would not be shown at all.
          cy.reload();

          // check that window.Fides.consent persists across page load
          cy.window()
            .its("Fides")
            .its("consent")
            .should("eql", {
              [PRIVACY_NOTICE_KEY_1]: true,
              [PRIVACY_NOTICE_KEY_2]: true,
            });
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
          [PRIVACY_NOTICE_KEY_1]: true,
          [PRIVACY_NOTICE_KEY_2]: true,
        };

        // check that consent was sent to Fides API
        cy.wait("@patchPrivacyPreference").then((interception) => {
          const { body } = interception.request;
          const expected = {
            browser_identity: { fides_user_device_id: uuid },
            preferences: [
              {
                privacy_notice_history_id:
                  "pri_b09058a7-9f54-4360-8da5-4521e8975d4f",
                preference: "opt_in",
              },
              {
                privacy_notice_history_id:
                  "pri_b09058a7-9f54-4360-8da5-4521e8975d4e",
                preference: "acknowledge",
              },
            ],
            privacy_experience_history_id: "2342345",
            user_geography: "us_ca",
            method: ConsentMethod.button,
          };
          expect(body).to.eql(expected);
        });

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
        cy.window().its("Fides").its("consent").should("eql", expectedConsent);
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

      it("fetches experience and renders the banner", () => {
        cy.wait("@getPrivacyExperience").then((interception) => {
          expect(interception.request.query.region).to.eq("us_ca");
        });
        cy.get("div#fides-consent-banner").should("exist");
        cy.contains("button", "Accept Test").should("exist");
        cy.get("div#fides-consent-banner.fides-consent-banner").within(() => {
          cy.get(
            "div#fides-consent-banner-description.fides-consent-banner-description"
          ).contains(
            "Config from mocked Fides API is overriding this banner description."
          );
        });
      });
      it("does not render modal link", () => {
        cy.get("#fides-consent-modal-link").should("not.be.visible");
      });
    });

    describe("when experience is provided, and geolocation is not provided", () => {
      beforeEach(() => {
        stubConfig({
          geolocation: OVERRIDE.EMPTY,
          options: {
            isGeolocationEnabled: true,
            geolocationApiUrl: "https://some-geolocation-url.com",
          },
        });
      });

      it("fetches geolocation and renders the banner", () => {
        // we still need geolocation because it is needed to save consent preference
        cy.wait("@getGeolocation");
        cy.get("div#fides-consent-banner").should("exist");
        cy.contains("button", "Accept Test").should("exist");
        cy.get("div#fides-consent-banner.fides-consent-banner").within(() => {
          cy.get(
            "div#fides-consent-banner-description.fides-consent-banner-description"
          ).contains(
            "This test website is overriding the banner description label."
          );
        });
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

        it("fetches geolocation and experience renders the banner", () => {
          cy.wait("@getGeolocation");
          cy.wait("@getPrivacyExperience").then((interception) => {
            expect(interception.request.query.region).to.eq("us_ca");
          });
          cy.get("div#fides-consent-banner").should("exist");
          cy.contains("button", "Accept Test").should("exist");
          cy.get("div#fides-consent-banner.fides-consent-banner").within(() => {
            cy.get(
              "div#fides-consent-banner-description.fides-consent-banner-description"
            ).contains(
              "Config from mocked Fides API is overriding this banner description."
            );
          });
        });
        it.skip("hides the modal link", () => {
          // TODO: add when we have link binding working
          expect(false).is.eql(true);
        });
      });

      describe("when geolocation is not successful", () => {
        beforeEach(() => {
          // mock failed geolocation api call
          const mockFailedGeolocationCall = {
            body: {},
          };
          stubConfig(
            {
              experience: OVERRIDE.EMPTY,
              geolocation: OVERRIDE.EMPTY,
              options: {
                isGeolocationEnabled: true,
                geolocationApiUrl: "https://some-geolocation-api.com",
              },
            },
            mockFailedGeolocationCall
          );
        });
        it("does not render banner", () => {
          cy.wait("@getGeolocation");
          cy.get("div#fides-consent-banner").should("not.exist");
          cy.contains("button", "Accept Test").should("not.exist");
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
            location: "",
            region: "",
          },
          options: {
            isGeolocationEnabled: true,
            geolocationApiUrl: "https://some-geolocation-api.com",
          },
        });
      });

      it("fetches geolocation and experience and renders the banner", () => {
        cy.wait("@getGeolocation");
        cy.wait("@getPrivacyExperience").then((interception) => {
          expect(interception.request.query.region).to.eq("us_ca");
        });
        cy.get("div#fides-consent-banner").should("exist");
        cy.contains("button", "Accept Test").should("exist");
        cy.get("div#fides-consent-banner.fides-consent-banner").within(() => {
          cy.get(
            "div#fides-consent-banner-description.fides-consent-banner-description"
          ).contains(
            "Config from mocked Fides API is overriding this banner description."
          );
        });
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

    describe("when all notices have current user preference set", () => {
      beforeEach(() => {
        stubConfig({
          experience: {
            privacy_notices: [
              {
                name: "Test privacy notice",
                disabled: false,
                origin: "12435134",
                description: "a test sample privacy notice configuration",
                internal_description:
                  "a test sample privacy notice configuration for internal use",
                regions: ["us_ca"],
                consent_mechanism: ConsentMechanism.OPT_IN,
                default_preference: UserConsentPreference.OPT_IN,
                current_preference: UserConsentPreference.OPT_IN,
                outdated_preference: null,
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
                privacy_notice_history_id:
                  "pri_b09058a7-9f54-4360-8da5-4521e8975d4f",
                notice_key: "advertising",
              },
            ],
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
