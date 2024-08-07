import { API_URL } from "../support/constants";

describe("Privacy request", () => {
  describe("when requesting data access", () => {
    beforeEach(() => {
      cy.intercept("POST", `${API_URL}/privacy-request`, {
        fixture: "privacy-request/unverified",
      }).as("postPrivacyRequest");
      cy.intercept(
        "POST",
        `${API_URL}/privacy-request/privacy-request-id/verify`,
        { body: {} },
      ).as("postPrivacyRequestVerify");
    });

    it("requires valid inputs", () => {
      cy.visit("/");
      cy.loadConfigFixture("config/config_all.json").then(() => {
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
});

describe("Privacy Request with custom fields with query params", () => {
  beforeEach(() => {
    cy.intercept("POST", `${API_URL}/privacy-request`, {
      fixture: "privacy-request/success",
    }).as("postPrivacyRequest");
  });

  it("displays a visible custom field, prefilled with the value from query param", () => {
    cy.visit("/?name=John");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_custom_request_fields.json").then(
      () => {
        cy.getByTestId("card").contains("Access your data").click();
        cy.getByTestId("privacy-request-form")
          .find("#name")
          .should("be.visible")
          .and("have.value", "John");
      },
    );
  });

  it("send hidden custom field as part of the request with the value from query param", () => {
    cy.visit("/?name=John&my_custom_app_id=123");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_custom_request_fields.json").then(
      () => {
        cy.getByTestId("card").contains("Access your data").click();

        cy.getByTestId("privacy-request-form")
          .find("#email")
          .type("test@test.com");

        cy.getByTestId("privacy-request-form")
          .find("button[type='submit']")
          .click();

        cy.wait("@postPrivacyRequest").then((interception) => {
          const customPrivacyRequestFields =
            interception.request.body[0].custom_privacy_request_fields;
          expect(customPrivacyRequestFields.my_custom_app_id.value).to.equal(
            "123",
          );
        });
      },
    );
  });

  it("uses default value if query param doesn't have a value", () => {
    cy.visit("/?name=John");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_custom_request_fields.json").then(
      () => {
        cy.getByTestId("card").contains("Access your data").click();

        cy.getByTestId("privacy-request-form")
          .find("#email")
          .type("test@test.com");

        cy.getByTestId("privacy-request-form")
          .find("button[type='submit']")
          .click();

        cy.wait("@postPrivacyRequest").then((interception) => {
          const customPrivacyRequestFields =
            interception.request.body[0].custom_privacy_request_fields;
          expect(
            customPrivacyRequestFields.another_custom_app_id.value,
          ).to.equal("12345");
        });
      },
    );
  });
});
