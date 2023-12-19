import {
  ComponentType,
  CONSENT_COOKIE_NAME,
  ConsentMechanism,
  ConsentMethod,
  ConsentOptionCreate,
  FidesCookie,
  LastServedConsentSchema,
  UserConsentPreference,
} from "fides-js";

import { RecordConsentServedRequest } from "fides-js/src/lib/consent-types";

import { mockPrivacyNotice } from "../support/mocks";

import { OVERRIDE, stubConfig } from "../support/stubs";

const PRIVACY_NOTICE_KEY_1 = "advertising";
const PRIVACY_NOTICE_KEY_2 = "essential";
const PRIVACY_NOTICE_KEY_3 = "analytics_opt_out";

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
            experience: OVERRIDE.UNDEFINED,
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
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_3)
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
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_3)
              .is.eql(false);
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
            cy.get("input").should("not.be.checked");
          });
          // Opt-out notice should start toggled on
          cy.getByTestId("toggle-Test privacy notice opt out").within(() => {
            cy.get("input").should("be.checked");
          });
          cy.getByTestId("toggle-Test privacy notice").click();
          // Notice-only should start off toggled on
          cy.getByTestId("toggle-Essential").within(() => {
            cy.get("input").should("be.checked");
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
                    "pri_b09058a7-9f54-4360-8da5-4521e89123fd",
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
              method: ConsentMethod.SAVE,
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
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_3)
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
              [PRIVACY_NOTICE_KEY_3]: true,
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
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });
        // Now reject all
        cy.getByTestId("fides-modal-content").within(() => {
          cy.get("button").contains("Reject Test").click();
        });
        // Check the modal again
        cy.get("[id='fides-modal-link']").click();
        cy.getByTestId("toggle-Test privacy notice").within(() => {
          cy.get("input").should("not.be.checked");
        });
        // Notice-only should still be checked
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });
      });

      it("handles legacy notices when experience fetched server-side", () => {
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

        // UI should reflect client-side fetched experience (test_banner_options.json)
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.disabled");
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Test privacy notice").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Test privacy notice opt out").within(() => {
          cy.get("input").should("be.checked");
        });

        // Save new preferences
        cy.getByTestId("toggle-Test privacy notice").click();
        cy.getByTestId("Save test-btn").click();

        // New privacy notice values only, no legacy ones
        const expectedConsent = {
          [PRIVACY_NOTICE_KEY_1]: true,
          [PRIVACY_NOTICE_KEY_2]: true,
          [PRIVACY_NOTICE_KEY_3]: true,
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
                  "pri_b09058a7-9f54-4360-8da5-4521e89123fd",
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
            method: ConsentMethod.SAVE,
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

      it("handles legacy notices when experience fetched client-side", () => {
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
          experience: OVERRIDE.UNDEFINED,
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
        });

        cy.contains("button", "Manage preferences").click();

        // UI should reflect client-side fetched experience (overlay_experience.json)
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });

        // Save new preferences
        cy.getByTestId("toggle-Advertising").click();
        cy.getByTestId("Confirm-btn").click();

        // New privacy notice values only, no legacy ones
        const expectedConsent = {
          advertising: true,
          analytics_opt_out: true,
        };

        // check that consent was sent to Fides API
        cy.wait("@patchPrivacyPreference").then((interception) => {
          const { body } = interception.request;
          const expected = {
            browser_identity: { fides_user_device_id: uuid },
            preferences: [
              {
                privacy_notice_history_id:
                  "pri_b2a0a2fa-ef59-4f7d-8e3d-d2e9bd076707",
                preference: "opt_in",
              },
              {
                privacy_notice_history_id:
                  "pri_b2a0a2fa-ef59-4f7d-8e3d-d2e9bd076239",
                preference: "opt_in",
              },
            ],
            privacy_experience_id: "pri_b9d1af04-5852-4499-bdfb-2778a6117fb8",
            user_geography: "us_ca",
            method: ConsentMethod.SAVE,
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
          cy.get("input").should("be.checked");
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
          cy.get("@FidesUpdated")
            .should("have.been.calledOnce")
            .its("lastCall.args.0.detail.extraDetails.consentMethod")
            .then((consentMethod) => {
              expect(consentMethod).to.eql(ConsentMethod.REJECT);
            });
          cy.getAllCookies().then((allCookies) => {
            expect(allCookies.map((c) => c.name)).to.eql([CONSENT_COOKIE_NAME]);
          });
        });

        it("can remove just the cookies associated with notices that were opted out", () => {
          cy.contains("button", "Manage preferences").click();
          // opt out of the first notice
          cy.getByTestId("toggle-one").click();
          cy.getByTestId("Save test-btn").click();
          cy.get("@FidesUpdated")
            .should("have.been.calledOnce")
            .its("lastCall.args.0.detail.extraDetails.consentMethod")
            .then((consentMethod) => {
              expect(consentMethod).to.eql(ConsentMethod.SAVE);
            });
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
            method: ConsentMethod.GPC,
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
          experience: OVERRIDE.UNDEFINED,
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
          geolocation: OVERRIDE.UNDEFINED,
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

    describe("when experience is empty, and geolocation is not provided", () => {
      beforeEach(() => {
        stubConfig({
          geolocation: OVERRIDE.UNDEFINED,
          experience: OVERRIDE.EMPTY,
          options: {
            isGeolocationEnabled: true,
            geolocationApiUrl: "https://some-geolocation-url.com",
          },
        });
      });

      it("does fetches geolocation and does not render the banner", () => {
        // we still need geolocation because it is needed to save consent preference
        cy.wait("@getGeolocation");
        cy.get("div#fides-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when experience is empty, and geolocation is provided", () => {
      beforeEach(() => {
        stubConfig({
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
          experience: OVERRIDE.EMPTY,
          options: {
            isGeolocationEnabled: true,
            geolocationApiUrl: "https://some-geolocation-url.com",
          },
        });
      });

      it("does not geolocate and does not render the banner", () => {
        cy.get("div#fides-banner").should("not.exist");
        cy.contains("button", "Accept Test").should("not.exist");
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when neither experience nor geolocation is provided, but geolocationApiUrl is defined", () => {
      describe("when geolocation is successful", () => {
        it("fetches geolocation and experience renders the banner", () => {
          const geoLocationUrl = "https://some-geolocation-api.com";
          stubConfig({
            experience: OVERRIDE.UNDEFINED,
            geolocation: OVERRIDE.UNDEFINED,
            options: {
              isGeolocationEnabled: true,
              geolocationApiUrl: geoLocationUrl,
            },
          });
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
          cy.get("#fides-modal-link").should("be.visible");
        });

        describe("when custom experience fn is provided in Fides.init()", () => {
          it("should skip calling Fides API cor experience and instead call the custom fn", () => {
            cy.fixture("consent/experience.json").then((privacyExperience) => {
              const apiOptions = {
                /* eslint-disable @typescript-eslint/no-unused-vars */
                getPrivacyExperienceFn: async (
                  userLocationString: string,
                  fidesUserDeviceId?: string | null
                ) => privacyExperience.items[0],
                /* eslint-enable @typescript-eslint/no-unused-vars */
              };
              const spyObject = cy.spy(apiOptions, "getPrivacyExperienceFn");
              stubConfig({
                options: {
                  isOverlayEnabled: true,
                  apiOptions,
                },
                geolocation: {
                  country: "US",
                  location: "US-CA",
                  region: "CA",
                },
                experience: OVERRIDE.UNDEFINED,
              });
              cy.waitUntilFidesInitialized().then(() => {
                // eslint-disable-next-line @typescript-eslint/no-unused-expressions
                expect(spyObject).to.be.called;
                const spy = spyObject.getCalls();
                const { args } = spy[0];
                expect(args[0]).to.equal("us_ca");
                // timeout means Fides API call not made, which is expected
                cy.on("fail", (error) => {
                  if (error.message.indexOf("Timed out retrying") !== 0) {
                    throw error;
                  }
                });
                // check that  Fides experience API is not called
                cy.wait("@getPrivacyExperience", {
                  requestTimeout: 100,
                }).then((xhr) => {
                  assert.isNull(xhr?.response?.body);
                });
              });
            });
          });
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
              experience: OVERRIDE.UNDEFINED,
              geolocation: OVERRIDE.UNDEFINED,
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
          experience: OVERRIDE.UNDEFINED,
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
          experience: OVERRIDE.UNDEFINED,
          geolocation: OVERRIDE.UNDEFINED,
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
    it("emits a FidesInitialized but not a FidesUpdated event when initialized", () => {
      cy.window()
        .its("Fides")
        .its("consent")
        .should("eql", {
          [PRIVACY_NOTICE_KEY_1]: false,
          [PRIVACY_NOTICE_KEY_2]: true,
          [PRIVACY_NOTICE_KEY_3]: true,
        });
      cy.get("@FidesInitialized")
        .should("have.been.calledOnce")
        .its("firstCall.args.0.detail.consent")
        .should("deep.equal", {
          [PRIVACY_NOTICE_KEY_1]: false,
          [PRIVACY_NOTICE_KEY_2]: true,
          [PRIVACY_NOTICE_KEY_3]: true,
        });
      cy.get("@FidesUpdated").should("not.have.been.called");
      cy.get("@FidesUIChanged").should("not.have.been.called");
    });

    describe("when preferences are changed / saved", () => {
      it("emits a FidesUpdated event when reject all is clicked", () => {
        cy.contains("button", "Reject Test").should("be.visible").click();
        cy.get("@FidesUIChanged").should("not.have.been.called");
        cy.get("@FidesInitialized")
          // First event, before the user rejects all
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_3]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
          });
        cy.get("@FidesUpdated")
          // Update event, when the user rejects all
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: false,
          });
        cy.get("@FidesUpdated")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.REJECT);
          });
      });

      it("emits a FidesUpdated event when accept all is clicked", () => {
        cy.contains("button", "Accept Test").should("be.visible").click();
        cy.get("@FidesUIChanged").should("not.have.been.called");
        cy.get("@FidesInitialized")
          // First event, before the user accepts all
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesUpdated")
          // Update event, when the user accepts all
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesUpdated")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.ACCEPT);
          });
      });

      it("emits a FidesUIChanged event when preferences are changed and a FidesUpdated event when preferences are saved", () => {
        cy.contains("button", "Manage preferences")
          .should("be.visible")
          .click();
        cy.getByTestId("toggle-Test privacy notice").click();
        cy.getByTestId("consent-modal").contains("Save").click();
        cy.get("@FidesUIChanged").should("have.been.calledOnce");
        cy.get("@FidesInitialized")
          // First event, before the user saved preferences
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });

        cy.get("@FidesUpdated")
          // Update event, when the user saved preferences and opted-in to the first notice
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesUpdated")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.SAVE);
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
              [PRIVACY_NOTICE_KEY_3]: true,
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
              [PRIVACY_NOTICE_KEY_3]: true,
            },
          },
        });
    });
  });

  describe("when listening for fides.js events with existing cookie", () => {
    describe("when overlay is enabled and legacy notices exist", () => {
      it("reflects client-side experiences consent in the UI", () => {
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
          experience: OVERRIDE.UNDEFINED,
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
        });
        cy.getCookie(CONSENT_COOKIE_NAME).should("exist");
        cy.contains("button", "Manage preferences").click();
        // Default preference opt-out
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        // Default preference opt-in
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });
      });

      // NOTE: See definition of cy.visitConsentDemo in commands.ts for where we
      // register listeners for these window events
      it("first event reflects legacy consent from cookie, second event reflects new experiences consent", () => {
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
        // There is a brief period of time when Fides.consent is set to the legacy values, but this
        // test asserts the new values have been set
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesInitialized")
          .should("have.been.calledTwice")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            data_sales: false,
            tracking: false,
            analytics: true,
          });
        cy.get("@FidesInitialized")
          .its("secondCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
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
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesInitialized")
          .should("have.been.calledTwice")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            data_sales: false,
            tracking: false,
            analytics: true,
          });
        cy.get("@FidesInitialized")
          .its("secondCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
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
          .should("have.been.calledTwice")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            data_sales: false,
            tracking: false,
            analytics: true,
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
          .should("have.been.calledTwice")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            data_sales: false,
            tracking: false,
            analytics: true,
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

  describe("consent reporting", () => {
    const experienceId = "experience-id";
    const historyId1 = "pri_mock_history_id_1";
    const historyId2 = "pri_mock_history_id_2";

    it("can go through consent reporting flow", () => {
      stubConfig({
        experience: {
          id: experienceId,
          show_banner: false,
          privacy_notices: [
            mockPrivacyNotice({
              name: "Data Sales and Sharing",
              notice_key: "data_sales_and_sharing",
              privacy_notice_history_id: historyId1,
            }),
            mockPrivacyNotice({
              name: "Essential",
              notice_key: "essential",
              privacy_notice_history_id: historyId2,
            }),
          ],
        },
      });
      cy.get("@FidesUIShown").should("not.have.been.called");
      cy.get("#fides-modal-link").click();
      cy.get("@FidesUIShown").should("have.been.calledOnce");
      cy.wait("@patchNoticesServed").then((interception) => {
        const { browser_identity: identity, ...body } =
          interception.request.body;
        expect(identity.fides_user_device_id).to.be.a("string");
        expect(body).to.eql({
          privacy_experience_id: experienceId,
          user_geography: "us_ca",
          acknowledge_mode: false,
          serving_component: "overlay",
          privacy_notice_history_ids: [historyId1, historyId2],
          tcf_purpose_consents: [],
          tcf_purpose_legitimate_interests: [],
          tcf_special_purposes: [],
          tcf_vendor_consents: [],
          tcf_vendor_legitimate_interests: [],
          tcf_features: [],
          tcf_special_features: [],
          tcf_system_consents: [],
          tcf_system_legitimate_interests: [],
        });
        // Now opt out of the notices
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Reject Test").click();
        });
        // The patch should include the served notice IDs (response from patchNoticesServed)
        cy.wait("@patchPrivacyPreference").then((preferenceInterception) => {
          const { preferences } = preferenceInterception.request.body;
          const expected = interception.response?.body.map(
            (s: LastServedConsentSchema) => s.served_notice_history_id
          );
          expect(
            preferences.map(
              (p: ConsentOptionCreate) => p.served_notice_history_id
            )
          ).to.eql(expected);
          expect(preferenceInterception.request.body.method).to.eql(
            ConsentMethod.REJECT
          );
        });
      });
    });

    it("can set acknowledge mode to true", () => {
      stubConfig({
        experience: {
          id: experienceId,
          show_banner: true,
          privacy_notices: [
            mockPrivacyNotice({
              name: "Data Sales and Sharing",
              notice_key: "data_sales_and_sharing",
              consent_mechanism: ConsentMechanism.NOTICE_ONLY,
              privacy_notice_history_id: historyId1,
            }),
            mockPrivacyNotice({
              name: "Essential",
              notice_key: "essential",
              consent_mechanism: ConsentMechanism.NOTICE_ONLY,
              privacy_notice_history_id: historyId2,
            }),
          ],
        },
      });
      cy.get("@FidesUIShown").should("have.been.calledOnce");
      cy.get("#fides-modal-link").click();
      cy.wait("@patchNoticesServed").then((interception) => {
        expect(interception.request.body.acknowledge_mode).to.eql(true);
      });
    });
    it("can call custom notices served fn instead of Fides API", () => {
      /* eslint-disable @typescript-eslint/no-unused-vars */
      const apiOptions = {
        patchNoticesServedFn: async (request: RecordConsentServedRequest) =>
          null,
      };
      /* eslint-enable @typescript-eslint/no-unused-vars */
      const spyObject = cy.spy(apiOptions, "patchNoticesServedFn");
      stubConfig({
        experience: {
          id: experienceId,
          show_banner: false,
          privacy_notices: [
            mockPrivacyNotice({
              name: "Data Sales and Sharing",
              notice_key: "data_sales_and_sharing",
              privacy_notice_history_id: historyId1,
            }),
            mockPrivacyNotice({
              name: "Essential",
              notice_key: "essential",
              privacy_notice_history_id: historyId2,
            }),
          ],
        },
        options: {
          apiOptions,
        },
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("not.have.been.called");
        cy.get("#fides-modal-link").click();
        cy.get("@FidesUIShown").then(() => {
          // eslint-disable-next-line @typescript-eslint/no-unused-expressions
          expect(spyObject).to.be.called;
          const spy = spyObject.getCalls();
          const { args } = spy[0];
          expect(args[0]).to.contains({
            serving_component: "overlay",
          });
          // timeout means API call not made, which is expected
          cy.on("fail", (error) => {
            if (error.message.indexOf("Timed out retrying") !== 0) {
              throw error;
            }
          });
          // check that notices aren't patched to Fides API
          cy.wait("@patchNoticesServed", {
            requestTimeout: 100,
          }).then((xhr) => {
            assert.isNull(xhr?.response?.body);
          });
        });
      });
    });
  });

  describe("consent overlay buttons", () => {
    it("only shows the save button when a single privacy notice is configured", () => {
      stubConfig({
        experience: {
          privacy_notices: [
            mockPrivacyNotice({
              name: "Marketing",
              has_gpc_flag: true,
            }),
          ],
        },
      });
      cy.get("button").contains("Manage preferences").click();
      cy.get(".fides-modal-button-group")
        .find("button")
        .should("have.length", 1);
    });
    it("shows all buttons when multiple privacy notices are configured", () => {
      stubConfig({
        experience: {
          privacy_notices: [
            mockPrivacyNotice({
              name: "Marketing",
              has_gpc_flag: true,
            }),
            mockPrivacyNotice({
              name: "Functional",
              has_gpc_flag: true,
            }),
          ],
        },
      });
      cy.get("button").contains("Manage preferences").click();
      cy.get(".fides-modal-button-group")
        .find("button")
        .should("have.length", 3);
    });
  });
});
