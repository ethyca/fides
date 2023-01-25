import { hostUrl } from "~/constants";
import { CONSENT_COOKIE_NAME } from "fides-consent";

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
        ],
      });
    });

    it("lets the user update their consent", () => {
      cy.visit("/consent");
      cy.getByTestId("consent");

      cy.getByTestId(`consent-item-card-advertising.first_party`).within(() => {
        cy.contains("Test advertising.first_party");
        cy.getRadio().should("not.be.checked");
      });
      cy.getByTestId(`consent-item-card-improve`).within(() => {
        cy.getRadio().should("be.checked");
      });

      // Consent to an item that was opted-out.
      cy.getByTestId(`consent-item-card-advertising`).within(() => {
        cy.getRadio().should("not.be.checked").check({ force: true });
      });
      cy.getByTestId("save-btn").click();

      cy.wait("@patchConsentPreferences").then((interception) => {
        const consent = interception.request.body.consent.find(
          (c: any) => c.data_use === "advertising"
        );
        expect(consent?.opt_in).to.eq(true);

        // there should be no browser identity
        expect(interception.request.body.browser_identity).to.eql(undefined);
      });

      // The cookie should also have been updated.
      cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
        const cookieKeyConsent = JSON.parse(decodeURIComponent(cookie!.value));
        expect(cookieKeyConsent.data_sales).to.eq(true);
      });
    });

    it("can grab the GA cookie and send to a consent request", () => {
      const clientId = "999999999.8888888888";
      const cookieValue = `GA1.1.${clientId}`;
      cy.setCookie("_ga", cookieValue);
      cy.visit("/consent");
      cy.getByTestId("consent");

      cy.getByTestId("save-btn").click();

      cy.wait("@patchConsentPreferences").then((interception) => {
        const { body } = interception.request;
        expect(body.browser_identity.ga_client_id).to.eq(clientId);
      });
    });

    it("reflects their choices using fides-consent.js", () => {
      // Opt-out of items default to opt-in.
      cy.visit("/consent");
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
  });
});
