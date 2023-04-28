import { hostUrl } from "~/constants";
import { CONSENT_COOKIE_NAME, FidesCookie } from "fides-consent";
import { GpcStatus } from "~/features/consent/types";
import { ConsentPreferencesWithVerificationCode } from "~/types/api";

describe("Consent settings", () => {
  describe("when the user isn't verified", () => {
    beforeEach(() => {
      cy.intercept("POST", `${hostUrl}/consent-request`, {
        body: {
          consent_request_id: "consent-request-id",
        },
      }).as("postConsentRequest");
      cy.intercept(
        "POST",
        `${hostUrl}/consent-request/consent-request-id/verify`,
        { fixture: "consent/verify" }
      ).as("postConsentRequestVerify");
    });

    it("can verify email and navigate to consent form", () => {
      cy.visit("/");
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
        cy.visit("/");
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        cy.getByTestId("card").contains("Manage your consent").click();
        cy.getByTestId("consent-request-form").within(() => {
          cy.get("input#email").type("test@example.com");
          cy.get("button").contains("Continue").click();
        });
        cy.wait("@postConsentRequest").then((interception) => {
          const { body } = interception.request;
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
            const cookie = JSON.parse(decodeURIComponent(cookieJson!.value)) as FidesCookie;
            expect(body.fides_user_device_id).to.eql(cookie.identity.fides_user_device_id);
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
        }
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
        cy.visit("/");
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
        }
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(previousCookie));
        cy.visit("/");
        cy.getByTestId("card").contains("Manage your consent").click();
        cy.getByTestId("consent-request-form").within(() => {
          cy.get("input#email").type("test@example.com");
          cy.get("button").contains("Continue").click();
        });
        cy.wait("@postConsentRequest").then((interception) => {
          const { body } = interception.request;
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
            const cookie = JSON.parse(decodeURIComponent(cookieJson!.value)) as FidesCookie;
            expect(body.fides_user_device_id).to.eql(cookie.identity.fides_user_device_id);
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
        `${hostUrl}/consent-request/consent-request-id/verify`,
        { fixture: "consent/verify" }
      ).as("postConsentRequestVerify");

      cy.intercept(
        "PATCH",
        `${hostUrl}/consent-request/consent-request-id/preferences`,
        (req) => {
          req.reply(req.body);
        }
      ).as("patchConsentPreferences");

      cy.visit("/consent");
      cy.getByTestId("consent");
      cy.dispatch({
        type: "config/overrideConsentOptions",
        payload: [
          {
            fidesDataUseKey: "advertising",
            name: "Test advertising",
            description: "",
            url: "https://example.com/privacy#data-sales",
            default: true,
            highlight: false,
            cookieKeys: ["data_sales"],
          },
          {
            fidesDataUseKey: "advertising.first_party",
            name: "Test advertising.first_party",
            description: "",
            url: "https://example.com/privacy#email-marketing",
            default: true,
            highlight: false,
            cookieKeys: ["tracking"],
          },
          {
            fidesDataUseKey: "improve",
            name: "Test improve",
            description: "",
            url: "https://example.com/privacy#analytics",
            default: true,
            highlight: false,
            cookieKeys: ["tracking"],
          },
          {
            fidesDataUseKey: "collect.gpc",
            name: "GPC test",
            description: "Just used for testing GPC.",
            url: "https://example.com/privacy#gpc",
            default: {
              value: true,
              globalPrivacyControl: false,
            },
            cookieKeys: ["gpc_test"],
          },
        ],
      });
    });

    it("lets the user update their consent", () => {
      cy.getByTestId("consent");

      cy.getByTestId(`consent-item-card-advertising.first_party`).within(() => {
        cy.contains("Test advertising.first_party");
        cy.getRadio().should("not.be.checked");
      });
      cy.getByTestId(`consent-item-card-improve`).within(() => {
        cy.getRadio().should("be.checked");
      });

      // Without GPC, this defaults to true.
      cy.getByTestId(`consent-item-card-collect.gpc`).within(() => {
        cy.getRadio().should("be.checked");
      });

      // Consent to an item that was opted-out.
      cy.getByTestId(`consent-item-card-advertising`).within(() => {
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

      // The cookie should also have been updated. This may take a moment in CI,
      // so we `waitUntil` the value becomes what we expect.
      // https://github.com/cypress-io/cypress/issues/4802#issuecomment-941891554
      cy.waitUntil(() =>
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
          const cookie = JSON.parse(decodeURIComponent(cookieJson!.value)) as FidesCookie;
          // `waitUntil` retries until we return a truthy value.
          return cookie.consent.data_sales === true;
        })
      );
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

    it("reflects their choices using fides-consent.js", () => {
      // Opt-out of items default to opt-in.
      cy.getByTestId(`consent-item-card-advertising`).within(() => {
        cy.getRadio("false").check({ force: true });
      });
      cy.getByTestId(`consent-item-card-improve`).within(() => {
        cy.getRadio("false").check({ force: true });
      });
      cy.getByTestId("save-btn").click();

      cy.visit("/fides-consent-demo.html");
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
      it("applies the GPC defaults", () => {
        cy.visit("/consent?globalPrivacyControl=true");
        cy.getByTestId("consent");

        cy.getByTestId("gpc-banner");

        cy.getByTestId(`consent-item-card-collect.gpc`).within(() => {
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
        cy.visit("/consent?globalPrivacyControl=true");
        cy.getByTestId("consent");

        cy.getByTestId("gpc-banner");

        cy.getByTestId(`consent-item-card-collect.gpc`).within(() => {
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
      cy.visit("/fides-consent-demo.html");
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
        cy.visit("/fides-consent-demo.html?globalPrivacyControl=true");
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
