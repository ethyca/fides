import {
  ComponentType,
  CONSENT_COOKIE_NAME,
  ConsentMethod,
  FidesCookie,
  LegacyConsentConfig,
  PrivacyNotice,
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
  mockGeolocationApiResp?: any,
  mockExperienceApiResp?: any
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
    // We conditionally stub these APIs because we need the exact API urls, which can change or not even exist
    // depending on the specific test case.
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
      const experienceResp = mockExperienceApiResp || {
        fixture: "consent/overlay_experience.json",
      };
      cy.intercept(
        "GET",
        `${updatedConfig.options.fidesApiUrl}${FidesEndpointPaths.PRIVACY_EXPERIENCE}*`,
        experienceResp
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

const mockPrivacyNotice = (params: Partial<PrivacyNotice>) => {
  const notice = {
    name: "Test privacy notice with GPC enabled",
    disabled: false,
    origin: "12435134",
    description: "a test sample privacy notice configuration",
    internal_description:
      "a test sample privacy notice configuration for internal use",
    regions: ["us_ca"],
    consent_mechanism: ConsentMechanism.OPT_OUT,
    default_preference: UserConsentPreference.OPT_IN,
    current_preference: undefined,
    outdated_preference: undefined,
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
    notice_key: "advertising",
    cookies: [],
  };
  return { ...notice, ...params };
};

const PRIVACY_NOTICE_KEY_1 = "advertising";
const PRIVACY_NOTICE_KEY_2 = "essential";

describe("Consent banner", () => {
  describe("when overlay is disabled", () => {
    describe("when both experience and legacy consent exist", () => {
      beforeEach(() => {
        stubConfig({
          options: {
            isOverlayEnabled: false,
          },
        });
      });
      it("sets Fides.consent object with default consent based on legacy consent", () => {
        cy.window().its("Fides").its("consent").should("eql", {
          data_sales: true,
          tracking: false,
        });
      });
      it("does not render banner", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });
      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when only legacy consent exists", () => {
      beforeEach(() => {
        stubConfig(
          {
            options: {
              isOverlayEnabled: false,
            },
            experience: OVERRIDE.EMPTY,
          },
          {},
          {}
        );
      });
      it("sets Fides.consent object with default consent based on legacy consent", () => {
        cy.window().its("Fides").its("consent").should("eql", {
          data_sales: true,
          tracking: false,
        });
      });
      it("does not render banner", () => {
        cy.get("div#fides-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });
      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });
  });

  describe("when user has no saved consent cookie", () => {
    describe("when overlay is enabled", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });
      });
      it("should render the expected HTML banner", () => {
        cy.get("div#fides-banner").within(() => {
          cy.get(
            "div#fides-banner-description.fides-banner-description"
          ).contains(
            "This test website is overriding the banner description label."
          );
          cy.get("div#fides-button-group").within(() => {
            cy.get(
              "button#fides-banner-button-tertiary.fides-banner-button.fides-banner-button-tertiary"
            ).contains("Manage preferences");
            cy.get(
              "button#fides-banner-button-primary.fides-banner-button.fides-banner-button-primary"
            ).contains("Reject Test");
            cy.get(
              "button#fides-banner-button-primary.fides-banner-button.fides-banner-button-primary"
            ).contains("Accept Test");
            // Order matters - it should always be secondary, then primary!
            cy.get("button")
              .eq(0)
              .should("have.id", "fides-banner-button-tertiary");
            cy.get("button")
              .eq(1)
              .should("have.id", "fides-banner-button-primary");
            cy.get("button")
              .eq(2)
              .should("have.id", "fides-banner-button-primary");
          });
        });
      });
      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
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

      it("should support rejecting all consent options but keeping notice-only true", () => {
        cy.contains("button", "Reject Test").should("be.visible").click();
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value)
            );
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_1)
              .is.eql(false);
            // Notice-only should stay true
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_2)
              .is.eql(true);
          });
        });
      });

      describe("modal", () => {
        it("should open modal when experience component = OVERLAY", () => {
          cy.contains("button", "Manage preferences").click();
          cy.getByTestId("consent-modal").should("be.visible");
        });

        it("can toggle the notices", () => {
          cy.contains("button", "Manage preferences").click();
          // Notice should start off toggled off
          cy.getByTestId("toggle-Test privacy notice").within(() => {
            cy.get("input").should("not.have.attr", "checked");
          });
          cy.getByTestId("toggle-Test privacy notice").click();
          // Notice-only should start off toggled on
          cy.getByTestId("toggle-Essential").within(() => {
            cy.get("input").should("have.attr", "checked");
          });

          cy.getByTestId("Save test-btn").click();
          // Modal should close after saving
          cy.getByTestId("consent-modal").should("not.be.visible");

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
              privacy_experience_id: "132345243",
              user_geography: "us_ca",
              method: ConsentMethod.button,
            };
            // uuid is generated automatically if the user has no saved consent cookie
            generatedUserDeviceId = body.browser_identity.fides_user_device_id;
            expect(generatedUserDeviceId).to.be.a("string");
            expect(body.preferences).to.eql(expected.preferences);
            expect(body.privacy_experience_id).to.eql(
              expected.privacy_experience_id
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
        });
      });

      it("can persist state between modal and banner", () => {
        cy.get("div#fides-banner").within(() => {
          cy.get("button").contains("Accept Test").click();
        });
        // Now check that the change persisted by opening the modal
        cy.get("[id='fides-modal-link']").click();
        cy.getByTestId("toggle-Test privacy notice").within(() => {
          cy.get("input").should("have.attr", "checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("have.attr", "checked");
        });
        // Now reject all
        cy.getByTestId("fides-modal-content").within(() => {
          cy.get("button").contains("Reject Test").click();
        });
        // Check the modal again
        cy.get("[id='fides-modal-link']").click();
        cy.getByTestId("toggle-Test privacy notice").within(() => {
          cy.get("input").should("not.have.attr", "checked");
        });
        // Notice-only should still be checked
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("have.attr", "checked");
        });
      });

      it("overwrites privacy notices that no longer exist", () => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        // we need to visit the page after the cookie exists, so the Fides.consent obj is initialized with the original
        // cookie values
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });

        cy.contains("button", "Manage preferences").click();

        // Save new preferences
        cy.getByTestId("toggle-Test privacy notice").click();
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.disabled");
        });
        cy.getByTestId("Save test-btn").click();

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
            privacy_experience_id: "132345243",
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

      it("disables notice-only notices from opting out", () => {
        cy.contains("button", "Manage preferences").click();
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.disabled");
          cy.get("input").should("have.attr", "checked");
        });
      });

      it.skip("should support option to display at top or bottom of page", () => {
        // TODO: add tests for top/bottom
        expect(false).is.eql(true);
      });

      it.skip("should support styling with CSS variables", () => {
        // TODO: add tests for CSS
        expect(false).is.eql(true);
      });

      describe("cookie enforcement", () => {
        beforeEach(() => {
          const cookies = [
            { name: "cookie1", path: "/" },
            { name: "cookie2", path: "/" },
          ];
          cookies.forEach((cookie) => {
            cy.setCookie(cookie.name, "value", { path: cookie.path });
          });
          stubConfig({
            experience: {
              privacy_notices: [
                mockPrivacyNotice({
                  name: "one",
                  privacy_notice_history_id: "one",
                  notice_key: "one",
                  consent_mechanism: ConsentMechanism.OPT_OUT,
                  cookies: [cookies[0]],
                }),
                mockPrivacyNotice({
                  name: "two",
                  privacy_notice_history_id: "two",
                  notice_key: "second",
                  consent_mechanism: ConsentMechanism.OPT_OUT,
                  cookies: [cookies[1]],
                }),
              ],
            },
            options: {
              isOverlayEnabled: true,
            },
          });
        });

        it("can remove all cookies when rejecting all", () => {
          cy.contains("button", "Reject Test").click();
          cy.getAllCookies().then((allCookies) => {
            expect(allCookies.map((c) => c.name)).to.eql([CONSENT_COOKIE_NAME]);
          });
        });

        it("can remove just the cookies associated with notices that were opted out", () => {
          cy.contains("button", "Manage preferences").click();
          // opt out of the first notice
          cy.getByTestId("toggle-one").click();
          cy.getByTestId("Save test-btn").click();
          cy.getAllCookies().then((allCookies) => {
            expect(allCookies.map((c) => c.name)).to.eql([
              CONSENT_COOKIE_NAME,
              "cookie2",
            ]);
          });
        });
      });
    });

    describe("when there are only notice-only notices", () => {
      const expected = [
        {
          privacy_notice_history_id: "one",
          preference: "acknowledge",
        },
        {
          privacy_notice_history_id: "two",
          preference: "acknowledge",
        },
      ];
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          experience: {
            privacy_notices: [
              mockPrivacyNotice({
                privacy_notice_history_id: "one",
                notice_key: "one",
                consent_mechanism: ConsentMechanism.NOTICE_ONLY,
              }),
              mockPrivacyNotice({
                privacy_notice_history_id: "two",
                notice_key: "second",
                consent_mechanism: ConsentMechanism.NOTICE_ONLY,
              }),
            ],
          },
          options: {
            isOverlayEnabled: true,
          },
        });
      });

      it("renders an acknowledge button in the banner", () => {
        cy.get("div#fides-banner").within(() => {
          cy.get("button").contains("OK");
          cy.get("button").contains("Accept Test").should("not.exist");
          cy.get("button").contains("OK").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.preferences).to.eql(expected);
          });
        });
      });

      it("renders an acknowledge button in the modal", () => {
        cy.get("#fides-modal-link").click();
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Accept Test").should("not.exist");
          cy.get("button").contains("OK").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.preferences).to.eql(expected);
          });
        });
      });
    });

    describe("when GPC flag is found, and notices apply to GPC", () => {
      beforeEach(() => {
        cy.on("window:before:load", (win) => {
          // eslint-disable-next-line no-param-reassign
          win.navigator.globalPrivacyControl = true;
        });
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          experience: {
            privacy_notices: [
              mockPrivacyNotice({
                name: "Test privacy notice with gpc enabled",
                has_gpc_flag: true,
              }),
            ],
          },
        });
      });
      it("sends GPC consent override downstream to Fides API", () => {
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
                preference: "opt_out",
              },
            ],
            privacy_experience_id: "132345243",
            user_geography: "us_ca",
            method: ConsentMethod.gpc,
          };
          // uuid is generated automatically if the user has no saved consent cookie
          generatedUserDeviceId = body.browser_identity.fides_user_device_id;
          expect(generatedUserDeviceId).to.be.a("string");
          expect(body.preferences).to.eql(expected.preferences);
          expect(body.privacy_experience_id).to.eql(
            expected.privacy_experience_id
          );
          expect(body.user_geography).to.eql(expected.user_geography);
          expect(body.method).to.eql(expected.method);
        });
      });

      it("stores consent in cookie", () => {
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value)
            );
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_1)
              .is.eql(false);
          });
        });
      });

      it("updates Fides consent obj", () => {
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
          });
      });

      it("shows indicators that GPC has been applied", () => {
        // In the banner
        cy.get("div#fides-banner").within(() => {
          cy.get("span").contains("Global Privacy Control Signal detected");
        });
        // And in the modal
        cy.get("button").contains("Manage preferences").click();
        cy.get("div.fides-gpc-banner").contains(
          "Global Privacy Control detected"
        );
        cy.get("span")
          .contains("Test privacy notice with gpc enabled")
          .parent()
          .within(() => {
            cy.get("span").contains("Global Privacy Control applied");
          });
      });
    });

    describe("when GPC flag is found, and no notices apply to GPC", () => {
      beforeEach(() => {
        cy.on("window:before:load", (win) => {
          // eslint-disable-next-line no-param-reassign
          win.navigator.globalPrivacyControl = true;
        });
        stubConfig({
          experience: {
            privacy_notices: [
              mockPrivacyNotice({
                name: "Test privacy notice with GPC disabled",
                has_gpc_flag: false,
              }),
            ],
          },
        });
      });
      it("does not set user consent preference automatically", () => {
        // timeout means API call not made, which is expected
        cy.on("fail", (error) => {
          if (error.message.indexOf("Timed out retrying") !== 0) {
            throw error;
          }
        });
        // check that preferences aren't sent to Fides API
        cy.wait("@patchPrivacyPreference", {
          requestTimeout: 500,
        }).then((xhr) => {
          assert.isNull(xhr?.response?.body);
        });
        // check that Fides consent obj is empty
        cy.window().its("Fides").its("consent").should("eql", {});
        // check that preferences do not exist in cookie
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      });

      it("does not show gpc indicator but does show it was detected and the info banner", () => {
        // In the banner
        cy.get("div.fides-gpc-banner").contains(
          "Global Privacy Control detected"
        );
        // And in the modal
        cy.get("button").contains("Manage preferences").click();
        cy.get("div.fides-gpc-banner").should("be.visible");
        cy.get("div.fides-gpc-badge").should("not.exist");
      });
    });

    describe("when no GPC flag is found, and notices apply to GPC", () => {
      beforeEach(() => {
        cy.on("window:before:load", (win) => {
          // eslint-disable-next-line no-param-reassign
          win.navigator.globalPrivacyControl = undefined;
        });
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          experience: {
            privacy_notices: [mockPrivacyNotice({ has_gpc_flag: true })],
          },
        });
      });

      it("does not set user consent preference automatically", () => {
        // timeout means API call not made, which is expected
        cy.on("fail", (error) => {
          if (error.message.indexOf("Timed out retrying") !== 0) {
            throw error;
          }
        });
        // check that preferences aren't sent to Fides API
        cy.wait("@patchPrivacyPreference", {
          requestTimeout: 500,
        }).then((xhr) => {
          assert.isNull(xhr?.response?.body);
        });
        // check that Fides consent obj is empty
        cy.window().its("Fides").its("consent").should("eql", {});
        // check that preferences do not exist in cookie
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      });

      it("does not show any gpc indicators", () => {
        // In the banner
        cy.get("div#fides-banner").within(() => {
          cy.get("span.fides-gpc-badge").should("not.exist");
        });
        // And in the modal
        cy.get("button").contains("Manage preferences").click();
        cy.get("div.fides-gpc-banner").should("not.exist");
        cy.get("div.fides-gpc-badge").should("not.exist");
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
        cy.get("div#fides-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });
      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
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
        cy.get("div#fides-banner").should("exist");
        cy.contains("button", "Accept Test").should("exist");
        cy.get("div#fides-banner").within(() => {
          cy.get(
            "div#fides-banner-description.fides-banner-description"
          ).contains(
            "Config from mocked Fides API is overriding this banner description."
          );
        });
      });
      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
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
        cy.get("div#fides-banner").should("exist");
        cy.contains("button", "Accept Test").should("exist");
        cy.get("div#fides-banner").within(() => {
          cy.get(
            "div#fides-banner-description.fides-banner-description"
          ).contains(
            "This test website is overriding the banner description label."
          );
        });
      });
      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
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
          cy.get("div#fides-banner").should("exist");
          cy.contains("button", "Accept Test").should("exist");
          cy.get("div#fides-banner").within(() => {
            cy.get(
              "div#fides-banner-description.fides-banner-description"
            ).contains(
              "Config from mocked Fides API is overriding this banner description."
            );
          });
        });
        it("shows the modal link", () => {
          cy.get("#fides-modal-link").should("be.visible");
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
          cy.get("div#fides-banner").should("not.exist");
          cy.contains("button", "Accept Test").should("not.exist");
        });
        it("hides the modal link", () => {
          cy.get("#fides-modal-link").should("not.be.visible");
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
        cy.get("div#fides-banner").should("exist");
        cy.contains("button", "Accept Test").should("exist");
        cy.get("div#fides-banner").within(() => {
          cy.get(
            "div#fides-banner-description.fides-banner-description"
          ).contains(
            "Config from mocked Fides API is overriding this banner description."
          );
        });
      });

      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
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
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
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
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when all notices have current user preference set and GPC flag exists", () => {
      beforeEach(() => {
        cy.on("window:before:load", (win) => {
          // eslint-disable-next-line no-param-reassign
          win.navigator.globalPrivacyControl = true;
        });
        stubConfig({
          experience: {
            privacy_notices: [
              mockPrivacyNotice({
                name: "Test privacy notice",
                has_gpc_flag: true,
                consent_mechanism: ConsentMechanism.OPT_IN,
                default_preference: UserConsentPreference.OPT_IN,
                current_preference: UserConsentPreference.OPT_IN,
              }),
            ],
          },
        });
      });

      it("does not render banner", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });

      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
      });

      it("does not set user consent preference automatically", () => {
        // timeout means API call not made, which is expected
        cy.on("fail", (error) => {
          if (error.message.indexOf("Timed out retrying") !== 0) {
            throw error;
          }
        });
        // check that preferences aren't sent to Fides API
        cy.wait("@patchPrivacyPreference", {
          requestTimeout: 500,
        }).then((xhr) => {
          assert.isNull(xhr?.response?.body);
        });
        // check that Fides consent obj is empty
        cy.window().its("Fides").its("consent").should("eql", {});
        // check that preferences do not exist in cookie
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      });

      it("shows gpc indicators in modal", () => {
        cy.get("#fides-modal-link").click();
        cy.get("div.fides-gpc-banner").contains(
          "Global Privacy Control detected"
        );
        cy.get("span")
          .contains("Test privacy notice")
          .parent()
          .within(() => {
            cy.get("span").contains("Global Privacy Control overridden");
          });
      });
    });

    describe("when banner should not be shown but modal link element exists", () => {
      beforeEach(() => {
        stubConfig({
          experience: {
            show_banner: false,
          },
        });
      });

      it("does not render banner", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });

      it("shows the modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
      });

      describe("modal link click", () => {
        it("should open modal", () => {
          cy.get("#fides-modal-link").should("be.visible").click();
          cy.getByTestId("consent-modal").should("be.visible");
        });
      });
    });

    describe("when both banner is shown and modal link element exists", () => {
      beforeEach(() => {
        stubConfig({
          experience: {
            show_banner: true,
          },
        });
      });

      it("closes banner and opens modal when modal link is clicked", () => {
        cy.get("div#fides-banner").should("be.visible");
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Accept Test").should("exist");
        });

        cy.get("#fides-modal-link").click();
        cy.get("div#fides-banner").should("not.be.visible");
        cy.getByTestId("consent-modal").should("be.visible");
      });

      it("opens modal even after modal has been previously opened and closed", () => {
        cy.reload();

        cy.contains("button", "Manage preferences").click();

        // Save new preferences
        cy.getByTestId("toggle-Test privacy notice").click();
        cy.getByTestId("toggle-Essential").click();
        cy.getByTestId("Save test-btn").click();

        cy.get("#fides-modal-link").click();
        cy.getByTestId("consent-modal").should("be.visible");
      });
    });
  });

  describe("when listening for fides.js events", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
      });
    });
    // NOTE: See definition of cy.visitConsentDemo in commands.ts for where we
    // register listeners for these window events
    it("emits both a FidesInitialized and FidesUpdated event when initialized", () => {
      cy.window()
        .its("Fides")
        .its("consent")
        .should("eql", {
          [PRIVACY_NOTICE_KEY_1]: false,
          [PRIVACY_NOTICE_KEY_2]: true,
        });
      cy.get("@FidesInitialized")
        .should("have.been.calledOnce")
        .its("firstCall.args.0.detail")
        .should("deep.equal", {
          consent: {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
          },
        });
      cy.get("@FidesUpdated")
        .should("have.been.calledOnce")
        .its("firstCall.args.0.detail")
        .should("deep.equal", {
          consent: {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
          },
        });
    });

    describe("when preferences are updated", () => {
      it("emits another FidesUpdated event when reject all is clicked", () => {
        cy.contains("button", "Reject Test").should("be.visible").click();
        cy.get("@FidesUpdated")
          .should("have.been.calledTwice")
          // First call should be from initialization, before the user rejects all
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: false,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          });
        cy.get("@FidesUpdated")
          // Second call is when the user rejects all
          .its("secondCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: false,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          });
      });

      it("emits another FidesUpdated event when accept all is clicked", () => {
        cy.contains("button", "Accept Test").should("be.visible").click();
        cy.get("@FidesUpdated")
          .should("have.been.calledTwice")
          // First call should be from initialization, before the user accepts all
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: false,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          });
        cy.get("@FidesUpdated")
          // Second call is when the user accepts all
          .its("secondCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: true,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          });
      });

      it("emits another FidesUpdated event when customized preferences are saved", () => {
        cy.contains("button", "Manage preferences")
          .should("be.visible")
          .click();
        cy.getByTestId("toggle-Test privacy notice").click();
        cy.getByTestId("consent-modal").contains("Save").click();
        cy.get("@FidesUpdated")
          .should("have.been.calledTwice")
          // First call should be from initialization, before the user saved preferences
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: false,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          });
        cy.get("@FidesUpdated")
          // Second call is when the user saved preferences and opted-in to the first notice
          .its("secondCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: true,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          });
      });
    });

    it("pushes events to the GTM integration", () => {
      cy.contains("button", "Accept Test").should("be.visible").click();
      cy.get("@dataLayerPush")
        .should("have.been.calledTwice")
        // First call should be from initialization, before the user accepts all
        .its("firstCall.args.0")
        .should("deep.equal", {
          event: "FidesInitialized",
          Fides: {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: false,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          },
        });
      cy.get("@dataLayerPush")
        // Second call is when the user accepts all
        .its("secondCall.args.0")
        .should("deep.equal", {
          event: "FidesUpdated",
          Fides: {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: true,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          },
        });
    });
  });
  describe("when listening for fides.js events with existing cookie", () => {
    describe("when overlay is enabled and legacy notices exist", () => {
      beforeEach(() => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        // we need to visit the page after the cookie exists, so the Fides.consent obj is initialized with the original
        // cookie values
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });
      });
      // NOTE: See definition of cy.visitConsentDemo in commands.ts for where we
      // register listeners for these window events
      it("first event reflects legacy consent from cookie, second event reflects new experiences consent", () => {
        // There is a brief period of time when Fides.consent is set to the legacy values, but this
        // test asserts the new values have been set
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
          });
        cy.get("@FidesInitialized")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
        cy.get("@FidesUpdated")
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
        cy.get("@FidesUpdated")
          .its("secondCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: false,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          });
      });
    });
    describe("when overlay is enabled and legacy notices do not exist", () => {
      beforeEach(() => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
          consent: { options: [] },
        });
      });
      it("first event reflects legacy cookie consent, second event reflects new experiences consent", () => {
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
          });
        cy.get("@FidesInitialized")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
        cy.get("@FidesUpdated")
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
        cy.get("@FidesUpdated")
          .its("secondCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              [PRIVACY_NOTICE_KEY_1]: false,
              [PRIVACY_NOTICE_KEY_2]: true,
            },
          });
      });
    });
    describe("when overlay is disabled and legacy notices do not exist", () => {
      beforeEach(() => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        stubConfig({
          options: {
            isOverlayEnabled: false,
          },
          consent: { options: [] },
        });
      });
      // NOTE: See definition of cy.visitConsentDemo in commands.ts for where we
      // register listeners for these window events
      it("all events should reflect existing legacy cookie values", () => {
        cy.window().its("Fides").its("consent").should("eql", {
          data_sales: false,
          tracking: false,
          analytics: true,
        });
        cy.get("@FidesInitialized")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
        cy.get("@FidesUpdated")
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
        cy.get("@FidesUpdated")
          .its("secondCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
      });
    });
    describe("when overlay is disabled and legacy notices exist", () => {
      beforeEach(() => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        stubConfig({
          options: {
            isOverlayEnabled: false,
          },
        });
      });
      // NOTE: See definition of cy.visitConsentDemo in commands.ts for where we
      // register listeners for these window events
      it("all events should reflect legacy consent from cookie", () => {
        cy.window().its("Fides").its("consent").should("eql", {
          data_sales: false,
          tracking: false,
          analytics: true,
        });
        cy.get("@FidesInitialized")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
        cy.get("@FidesUpdated")
          .its("firstCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
        cy.get("@FidesUpdated")
          .its("secondCall.args.0.detail")
          .should("deep.equal", {
            consent: {
              data_sales: false,
              tracking: false,
              analytics: true,
            },
          });
      });
    });
  });

  describe("gpc indicators in the modal", () => {
    beforeEach(() => {
      cy.on("window:before:load", (win) => {
        // eslint-disable-next-line no-param-reassign
        win.navigator.globalPrivacyControl = true;
      });
    });
    it("renders the proper gpc indicator", () => {
      stubConfig({
        experience: {
          privacy_notices: [
            mockPrivacyNotice({
              name: "Applied",
              notice_key: "applied",
              has_gpc_flag: true,
              consent_mechanism: ConsentMechanism.OPT_OUT,
              default_preference: UserConsentPreference.OPT_IN,
              current_preference: undefined,
            }),
            mockPrivacyNotice({
              name: "Notice only",
              notice_key: "notice_only",
              // notice-only should never have has_gpc_flag true, but just in case,
              // make sure the expected behavior still holds if it is somehow true
              has_gpc_flag: true,
              consent_mechanism: ConsentMechanism.NOTICE_ONLY,
              default_preference: UserConsentPreference.ACKNOWLEDGE,
              current_preference: UserConsentPreference.ACKNOWLEDGE,
            }),
            mockPrivacyNotice({
              name: "Overridden",
              notice_key: "overridden",
              has_gpc_flag: true,
              consent_mechanism: ConsentMechanism.OPT_OUT,
              default_preference: UserConsentPreference.OPT_IN,
              current_preference: UserConsentPreference.OPT_IN,
            }),
          ],
        },
      });
      cy.get("#fides-modal-link").click();
      cy.get(".fides-notice-toggle")
        .contains("Applied")
        .parent()
        .within(() => {
          cy.get(".fides-gpc-label").contains("applied");
        });
      cy.get(".fides-notice-toggle")
        .contains("Notice only")
        .parent()
        .within(() => {
          cy.get(".fides-gpc-label").should("not.exist");
        });
      cy.get(".fides-notice-toggle")
        .contains("Overridden")
        .parent()
        .within(() => {
          cy.get(".fides-gpc-label").contains("overridden");
        });
    });
  });
});
