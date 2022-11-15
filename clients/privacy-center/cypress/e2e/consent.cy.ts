import { hostUrl } from "~/constants";
import { CONSENT_COOKIE_NAME } from "~/features/consent/cookie";

describe("Consent settings", () => {
  beforeEach(() => {
    // All of these tests assume identity verification is required.
    cy.intercept("GET", `${hostUrl}/id-verification/config`, {
      body: {
        identity_verification_required: true,
      },
    }).as("getVerificationConfig");
  });

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
        cy.get("input").type("test@example.com");
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
    });

    it("lets the user update their consent", () => {
      cy.visit("/consent");
      cy.getByTestId("consent");

      cy.getByTestId(`consent-item-card-advertising.first_party`).within(() => {
        cy.get('input[type="radio"][value="true"]').should("not.be.checked");
      });
      cy.getByTestId(`consent-item-card-improve`).within(() => {
        cy.get('input[type="radio"][value="true"]').should("be.checked");
      });

      // Consent to an item that was opted-out.
      cy.getByTestId(`consent-item-card-advertising`).within(() => {
        cy.get('input[type="radio"][value="true"]')
          .should("not.be.checked")
          .check({ force: true });
      });

      cy.intercept(
        "PATCH",
        `${hostUrl}/consent-request/consent-request-id/preferences/`,
        (req) => {
          const consent = req.body.consent.find(
            (c: any) => c.data_use === "advertising"
          );
          expect(consent?.opt_in).to.eq(true);
          req.reply(req.body);
        }
      ).as("patchConsentPreferences");
      cy.getByTestId("save-btn").click();
      cy.wait("@patchConsentPreferences");

      // The cookie should also have been updated.
      cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
        const cookieKeyConsent = JSON.parse(decodeURIComponent(cookie!.value));
        expect(cookieKeyConsent.data_sales).to.eq(true);
      });
    });
  });
});
