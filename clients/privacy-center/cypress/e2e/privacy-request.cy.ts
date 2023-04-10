import { hostUrl } from "~/constants";

describe("Privacy request", () => {
  describe("when requesting data access", () => {
    beforeEach(() => {
      cy.intercept("POST", `${hostUrl}/privacy-request`, {
        fixture: "privacy-request/unverified",
      }).as("postPrivacyRequest");
      cy.intercept(
        "POST",
        `${hostUrl}/privacy-request/privacy-request-id/verify`,
        { body: {} }
      ).as("postPrivacyRequestVerify");
    });

    it("requires valid inputs", () => {
      cy.visit("/");
      cy.getByTestId("card").contains("Access your data").click();

      cy.getByTestId("privacy-request-form").within(() => {
        // This block uses `.root()` to keep queries within the form. This is necessary because of
        // `.blur()` which triggers input validation.

        // test email being typed, continue becoming disabled due to invalid email
        cy.root().get("input#email").type("invalid email").blur();
        cy.root().should("contain", "Email is invalid");
        cy.root().get("button").contains("Continue").should("be.disabled");
        cy.root().get("input#email").clear().blur();

        // test valid email, continue becoming enabled due to valid email
        cy.root().get("input#email").type("valid@example.com").blur();
        cy.root().get("button").contains("Continue").should("be.enabled");
        cy.root().get("input#email").clear().blur();
      });
    });
  });
});
