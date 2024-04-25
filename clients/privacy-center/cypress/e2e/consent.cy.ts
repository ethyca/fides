import { CONSENT_COOKIE_NAME, FidesCookie, GpcStatus } from "fides-js";
import { ConsentPreferencesWithVerificationCode } from "~/types/api";
import { API_URL } from "../support/constants";

describe("Consent modal deeplink", () => {
  beforeEach(() => {
    cy.visit("/?showConsentModal=true");
    cy.loadConfigFixture("config/config_consent.json").as("config");
    cy.overrideSettings({ IS_OVERLAY_ENABLED: false });
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

  it("opens the consent modal", () => {
    // This test does the same as below, without clicking the card
    cy.getByTestId("consent-request-form").should("be.visible");
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

  it("closes the modal and purges the query param", () => {
    cy.getByTestId("consent-request-form").should("be.visible");

    cy.getByTestId("consent-request-form").within(() => {
      cy.get("input#email").type("test@example.com");
      cy.get("button").contains("Cancel").click();
    });

    // assert the modal is closed and query_param removed
    cy.url().should("not.contain", "showConsentModal=true");
    cy.getByTestId("consent-request-form").should("not.exist");
  });
});

describe("Consent settings", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.loadConfigFixture("config/config_consent.json").as("config");
    cy.overrideSettings({ IS_OVERLAY_ENABLED: false });
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
            expect(body.identity.fides_user_device_id).to.eql(
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
          expect(body.identity.fides_user_device_id).to.eql(uuid);
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
            expect(body.identity.fides_user_device_id).to.eql(
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
      cy.overrideSettings({ IS_OVERLAY_ENABLED: false });
    });

    it("populates its header and description from config", () => {
      cy.getByTestId("consent-heading").contains("Manage your consent");
      cy.getByTestId("consent-description").contains(
        "Test your consent preferences"
      );
      cy.getByTestId("consent-description").contains("When you use our");
    });

    it("lets the user update their consent", () => {
      cy.getByTestId("consent");

      cy.getByTestId(`consent-item-advertising.first_party`).within(() => {
        cy.contains("Test advertising.first_party");
        cy.getRadio().should("not.be.checked");
      });
      cy.getByTestId(`consent-item-functional`).within(() => {
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

        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME);
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
          const cookie = JSON.parse(
            decodeURIComponent(cookieJson!.value)
          ) as FidesCookie;
          expect(cookie.consent.data_sales).to.eql(true);
        });
      });
    });

    it("can grab cookies and send to a consent request", () => {
      const clientId = "999999999.8888888888";
      const gaCookieValue = `GA1.1.${clientId}`;
      const sovrnCookieValue = "test";

      cy.setCookie("_ga", gaCookieValue);
      cy.setCookie("ljt_readerID", sovrnCookieValue);
      cy.getByTestId("save-btn").click();

      cy.wait("@patchConsentPreferences").then((interception) => {
        const body = interception.request
          .body as ConsentPreferencesWithVerificationCode;
        expect(body.browser_identity?.ga_client_id).to.eq(clientId);
        expect(body.browser_identity?.ljt_readerID).to.eq(sovrnCookieValue);
      });
    });

    /**
     * TODO (PROD-1748): update this test to *override* the config to not rely
     * on any local ENV settings for the running Privacy Center... right now
     * this'll fail if you set FIDES_PRIVACY_CENTER__IS_OVERLAY_ENABLED=true on
     * your local Privacy Center, because the cy.visit("/fides-js-demo.html")
     * doesn't obey the overrideSettings above.
     */
    it("reflects their choices using fides.js", () => {
      // Opt-out of items default to opt-in.
      cy.getByTestId(`consent-item-advertising`).within(() => {
        cy.getRadio("false").check({ force: true });
      });
      cy.getByTestId(`consent-item-functional`).within(() => {
        cy.getRadio("false").check({ force: true });
      });
      cy.getByTestId("save-btn").click();

      cy.visit("/fides-js-demo.html");
      cy.get("#consent-json");
      cy.waitUntilFidesInitialized().then(() => {
        cy.window({ timeout: 1000 }).should("have.property", "dataLayer");
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
            .to.have.nested.property("dataLayer[0]")
            .that.eql({
              event: "FidesInitialized",
              Fides: {
                consent: {
                  data_sales: false,
                  tracking: false,
                  analytics: true,
                  gpc_test: true,
                },
              },
            });

          // Meta Pixel configuration
          expect(win)
            .to.have.nested.property("fbq.queue")
            .that.eql([
              ["consent", "revoke"],
              ["dataProcessingOptions", ["LDU"], 1, 1000],
            ]);
        });
      });
    });

    describe("when globalPrivacyControl is enabled", () => {
      beforeEach(() => {
        cy.visit("/consent?globalPrivacyControl=true");
        cy.getByTestId("consent");
        cy.loadConfigFixture("config/config_consent.json").as("config");
        cy.overrideSettings({ IS_OVERLAY_ENABLED: false });
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

  /**
   * TODO (PROD-1748): update this test to *override* the config to not rely
   * on any local ENV settings for the running Privacy Center... right now
   * this'll fail if you set FIDES_PRIVACY_CENTER__IS_OVERLAY_ENABLED=true on
   * your local Privacy Center, because the cy.visit("/fides-js-demo.html")
   * doesn't obey the overrideSettings above.
   */
  describe("when the user hasn't modified their consent", () => {
    it("reflects the defaults from config.json", () => {
      cy.visit("/fides-js-demo.html");
      cy.get("#consent-json");
      cy.waitUntilFidesInitialized().then(() => {
        cy.window({ timeout: 1000 }).should("have.property", "dataLayer");
        cy.window().then((win) => {
          // Before visiting the privacy center the consent object only has the default choices.
          expect(win).to.have.nested.property("Fides.consent").that.eql({
            data_sales: true,
            tracking: true,
            analytics: true,
          });

          // GTM configuration
          expect(win)
            .to.have.nested.property("dataLayer[0]")
            .that.eql({
              event: "FidesInitialized",
              Fides: {
                consent: {
                  data_sales: true,
                  tracking: true,
                  analytics: true,
                },
              },
            });

          // Meta Pixel configuration
          expect(win)
            .to.have.nested.property("fbq.queue")
            .that.eql([
              ["consent", "grant"],
              ["dataProcessingOptions", []],
            ]);
        });
      });
    });

    /**
     * TODO (PROD-1748): update this test to *override* the config to not rely
     * on any local ENV settings for the running Privacy Center... right now
     * this'll fail if you set FIDES_PRIVACY_CENTER__IS_OVERLAY_ENABLED=true on
     * your local Privacy Center, because the cy.visit("/fides-js-demo.html")
     * doesn't obey the overrideSettings above.
     */
    describe("when globalPrivacyControl is enabled", () => {
      it("uses the globalPrivacyControl default", () => {
        cy.visit("/fides-js-demo.html?globalPrivacyControl=true");
        cy.get("#consent-json");
        cy.waitUntilFidesInitialized().then(() => {
          cy.window({ timeout: 1000 }).should("have.property", "dataLayer");
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
});
