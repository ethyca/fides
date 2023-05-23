import { CONSENT_COOKIE_NAME, FidesCookie } from "fides-js";
import { GpcStatus } from "~/features/consent/types";
import { ConsentPreferencesWithVerificationCode } from "~/types/api";
import { API_URL } from "../support/constants";

describe("Consent settings", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.loadConfigFixture("config/config_consent.json").as("config");
  });

  describe("when the user isn't verified", () => {
    beforeEach(() => {
      cy.intercept("POST", `${API_URL}/consent-request`, {
        body: {
          consent_request_id: "consent-request-id",
        },
      }).as("postConsentRequest");
      cy.intercept(
        "POST",
        `${API_URL}/consent-request/consent-request-id/verify`,
        { fixture: "consent/verify" }
      ).as("postConsentRequestVerify");
    });

    it("can verify email and navigate to consent form", () => {
      cy.getByTestId("card").contains("Manage your consent").click();

      cy.getByTestId("consent-request-form").within(() => {
        cy.get("input#email").type("test@example.com");
        cy.get("button").contains("Continue").click();
      });
      cy.wait("@postConsentRequest");

      cy.getByTestId("verification-form").within(() => {
        cy.get("input").type("112358");
        cy.get("button").contains("Submit code").click();
      });
      cy.wait("@postConsentRequestVerify");

      cy.location("pathname").should("eq", "/consent");
      cy.getByTestId("consent");
    });

    it("redirects to the homepage", () => {
      cy.visit("/consent");
      cy.location("pathname").should("eq", "/");
      cy.getByTestId("home");
    });

    describe("device uuid", () => {
      it("can send a device uuid when there is no cookie", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        cy.getByTestId("card").contains("Manage your consent").click();
        cy.getByTestId("consent-request-form").within(() => {
          cy.get("input#email").type("test@example.com");
          cy.get("button").contains("Continue").click();
        });
        cy.wait("@postConsentRequest").then((interception) => {
          const { body } = interception.request;
          cy.waitUntilCookieExists(CONSENT_COOKIE_NAME);
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
            const cookie = JSON.parse(
              decodeURIComponent(cookieJson!.value)
            ) as FidesCookie;
            expect(body.fides_user_device_id).to.eql(
              cookie.identity.fides_user_device_id
            );
          });
        });
      });

      it("can send a device uuid when a cookie exists", () => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const now = "2023-04-28T12:00:00.000Z";
        const cookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: { version: "0.9.0", createdAt: now },
          consent: {},
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
        cy.getByTestId("card").contains("Manage your consent").click();
        cy.getByTestId("consent-request-form").within(() => {
          cy.get("input#email").type("test@example.com");
          cy.get("button").contains("Continue").click();
        });
        cy.wait("@postConsentRequest").then((interception) => {
          const { body } = interception.request;
          expect(body.fides_user_device_id).to.eql(uuid);
        });
      });

      it("can read previous versions of the cookie and add a device uuid", () => {
        const previousCookie = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(previousCookie));
        cy.getByTestId("card").contains("Manage your consent").click();
        cy.getByTestId("consent-request-form").within(() => {
          cy.get("input#email").type("test@example.com");
          cy.get("button").contains("Continue").click();
        });
        cy.wait("@postConsentRequest").then((interception) => {
          const { body } = interception.request;
          // Wait until the cookie is updated to the new format
          cy.waitUntil(() =>
            cy
              .getCookie(CONSENT_COOKIE_NAME)
              .then((cookie) =>
                Boolean(cookie!.value && cookie!.value.match(/identity/))
              )
          );
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
            const cookie = JSON.parse(
              decodeURIComponent(cookieJson!.value)
            ) as FidesCookie;
            expect(body.fides_user_device_id).to.eql(
              cookie.identity.fides_user_device_id
            );
            expect(cookie.consent).to.eql(previousCookie);
          });
        });
      });
    });
  });

  describe("when the user is already verified", () => {
    beforeEach(() => {
      cy.window().then((win) => {
        win.localStorage.setItem(
          "consentRequestId",
          JSON.stringify("consent-request-id")
        );
        win.localStorage.setItem("verificationCode", JSON.stringify("112358"));
      });

      // Consent items are returned by the verify endpoint.
      cy.intercept(
        "POST",
        `${API_URL}/consent-request/consent-request-id/verify`,
        { fixture: "consent/verify" }
      ).as("postConsentRequestVerify");

      cy.intercept("GET", `${API_URL}/privacy-experience/*`, {
        fixture: "consent/experience.json",
      }).as("getExperience");

      cy.intercept(
        "PATCH",
        `${API_URL}/consent-request/consent-request-id/preferences`,
        (req) => {
          req.reply(req.body);
        }
      ).as("patchConsentPreferences");

      cy.visit("/consent");
      cy.getByTestId("consent");
      cy.loadConfigFixture("config/config_consent.json").as("config");
    });

    it("renders from privacy notices", () => {
      cy.overrideSettings({
        IS_OVERLAY_DISABLED: false,
      });
      // Opt in, so default to not checked
      const PRIVACY_NOTICE_ID_1 = "pri_2d1e758a-2678-4a7c-a514-fbf97a994e66";
      // Opt out, so default to checked
      const PRIVACY_NOTICE_ID_2 = "pri_9d60c347-af22-44d0-bcbb-9a4007c3e08e";
      cy.getByTestId("consent");
      cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
        cy.getRadio().should("not.be.checked");
      });
      cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_2}`).within(() => {
        cy.getRadio().should("be.checked");
      });

      // Opt out of the opt in notice
      cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
        cy.getRadio().should("not.be.checked").check({ force: true });
      });
    });

    it("lets the user update their consent", () => {
      cy.getByTestId("consent");

      cy.getByTestId(`consent-item-advertising.first_party`).within(() => {
        cy.contains("Test advertising.first_party");
        cy.getRadio().should("not.be.checked");
      });
      cy.getByTestId(`consent-item-improve`).within(() => {
        cy.getRadio().should("be.checked");
      });

      // Without GPC, this defaults to true.
      cy.getByTestId(`consent-item-collect.gpc`).within(() => {
        cy.getRadio().should("be.checked");
      });

      // Consent to an item that was opted-out.
      cy.getByTestId(`consent-item-advertising`).within(() => {
        cy.getRadio().should("not.be.checked").check({ force: true });
      });
      cy.getByTestId("save-btn").click();

      cy.wait("@patchConsentPreferences").then((interception) => {
        const body = interception.request
          .body as ConsentPreferencesWithVerificationCode;

        const advertisingConsent = body.consent.find(
          (c) => c.data_use === "advertising"
        );
        expect(advertisingConsent?.opt_in).to.eq(true);

        const gpcConsent = body.consent.find(
          (c) => c.data_use === "collect.gpc"
        );
        expect(gpcConsent?.opt_in).to.eq(true);
        expect(gpcConsent?.has_gpc_flag).to.eq(false);
        expect(gpcConsent?.conflicts_with_gpc).to.eq(false);

        // there should be no browser identity
        expect(body.browser_identity).to.eql(undefined);
      });

      cy.waitUntilCookieExists(CONSENT_COOKIE_NAME);
      cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
        const cookie = JSON.parse(
          decodeURIComponent(cookieJson!.value)
        ) as FidesCookie;
        expect(cookie.consent.data_sales).to.eql(true);
      });
    });

    it("can grab cookies and send to a consent request", () => {
      const clientId = "999999999.8888888888";
      const gaCookieValue = `GA1.1.${clientId}`;
      const sovrnCookieValue = "test";

      cy.setCookie("_ga", gaCookieValue);
      cy.setCookie("ljt_readerID", sovrnCookieValue);
      cy.visit("/consent");
      cy.getByTestId("consent");

      cy.getByTestId("save-btn").click();

      cy.wait("@patchConsentPreferences").then((interception) => {
        const body = interception.request
          .body as ConsentPreferencesWithVerificationCode;
        expect(body.browser_identity?.ga_client_id).to.eq(clientId);
        expect(body.browser_identity?.ljt_readerID).to.eq(sovrnCookieValue);
      });
    });

    it("reflects their choices using fides.js", () => {
      // Opt-out of items default to opt-in.
      cy.getByTestId(`consent-item-advertising`).within(() => {
        cy.getRadio("false").check({ force: true });
      });
      cy.getByTestId(`consent-item-improve`).within(() => {
        cy.getRadio("false").check({ force: true });
      });
      cy.getByTestId("save-btn").click();

      cy.visit("/fides-js-demo.html");
      cy.get("#consent-json");
      cy.window().then((win) => {
        // Now all of the cookie keys should be populated.
        expect(win).to.have.nested.property("Fides.consent").that.eql({
          data_sales: false,
          tracking: false,
          analytics: true,
          gpc_test: true,
        });

        // GTM configuration
        expect(win)
          .to.have.nested.property("dataLayer")
          .that.eql([
            {
              Fides: {
                consent: {
                  data_sales: false,
                  tracking: false,
                  analytics: true,
                  gpc_test: true,
                },
              },
            },
          ]);

        // Meta Pixel configuration
        expect(win)
          .to.have.nested.property("fbq.queue")
          .that.eql([
            ["consent", "revoke"],
            ["dataProcessingOptions", ["LDU"], 1, 1000],
          ]);
      });
    });

    describe("when globalPrivacyControl is enabled", () => {
      beforeEach(() => {
        cy.visit("/consent?globalPrivacyControl=true");
        cy.getByTestId("consent");
        cy.loadConfigFixture("config/config_consent.json").as("config");
      });

      it("applies the GPC defaults", () => {
        cy.getByTestId("gpc-banner");
        cy.getByTestId(`consent-item-collect.gpc`).within(() => {
          cy.contains("GPC test");
          cy.getRadio().should("not.be.checked");
          cy.getByTestId("gpc-badge").should("contain", GpcStatus.APPLIED);
        });

        cy.getByTestId("save-btn").click();

        cy.wait("@patchConsentPreferences").then((interception) => {
          const body = interception.request
            .body as ConsentPreferencesWithVerificationCode;

          const gpcConsent = body.consent.find(
            (c) => c.data_use === "collect.gpc"
          );
          expect(gpcConsent?.opt_in).to.eq(false);
          expect(gpcConsent?.has_gpc_flag).to.eq(true);
          expect(gpcConsent?.conflicts_with_gpc).to.eq(false);
        });
      });

      it("lets the user consent to override GPC", () => {
        cy.getByTestId("gpc-banner");
        cy.getByTestId(`consent-item-collect.gpc`).within(() => {
          cy.contains("GPC test");
          cy.getRadio().should("not.be.checked").check({ force: true });
          cy.getByTestId("gpc-badge").should("contain", GpcStatus.OVERRIDDEN);
        });
        cy.getByTestId("save-btn").click();

        cy.wait("@patchConsentPreferences").then((interception) => {
          const body = interception.request
            .body as ConsentPreferencesWithVerificationCode;

          const gpcConsent = body.consent.find(
            (c) => c.data_use === "collect.gpc"
          );
          expect(gpcConsent?.opt_in).to.eq(true);
          expect(gpcConsent?.has_gpc_flag).to.eq(true);
          expect(gpcConsent?.conflicts_with_gpc).to.eq(true);
        });
      });
    });
  });

  describe("when the user hasn't modified their consent", () => {
    it("reflects the defaults from config.json", () => {
      cy.visit("/fides-js-demo.html");
      cy.get("#consent-json");
      cy.window().then((win) => {
        // Before visiting the privacy center the consent object only has the default choices.
        expect(win).to.have.nested.property("Fides.consent").that.eql({
          data_sales: true,
          tracking: true,
          analytics: true,
        });

        // GTM configuration
        expect(win)
          .to.have.nested.property("dataLayer")
          .that.eql([
            {
              Fides: {
                consent: {
                  data_sales: true,
                  tracking: true,
                  analytics: true,
                },
              },
            },
          ]);

        // Meta Pixel configuration
        expect(win)
          .to.have.nested.property("fbq.queue")
          .that.eql([
            ["consent", "grant"],
            ["dataProcessingOptions", []],
          ]);
      });
    });

    describe("when globalPrivacyControl is enabled", () => {
      it("uses the globalPrivacyControl default", () => {
        cy.visit("/fides-js-demo.html?globalPrivacyControl=true");
        cy.get("#consent-json");
        cy.window().then((win) => {
          expect(win).to.have.nested.property("Fides.consent").that.eql({
            data_sales: false,
            tracking: false,
            analytics: true,
          });
        });
      });
    });
  });
});
