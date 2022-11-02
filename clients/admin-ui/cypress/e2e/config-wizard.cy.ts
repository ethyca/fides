import { stubSystemCrud, stubTaxonomyEntities } from "cypress/support/stubs";

// skipping while configWizardFlag exists
describe.skip("Config Wizard", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/organization/*", {
      fixture: "organization.json",
    }).as("getOrganization");

    cy.intercept("PUT", "/api/v1/organization**", {
      fixture: "organization.json",
    }).as("updateOrganization");
  });

  beforeEach(() => {
    cy.visit("/config-wizard");
    cy.getByTestId("guided-setup-btn").click();
    cy.wait("@getOrganization");
  });

  describe("Organization setup", () => {
    it("Fills in the default organization", () => {
      cy.getByTestId("organization-info-form");
      cy.getByTestId("input-name").should("have.value", "Demo Organization");
      cy.getByTestId("input-description")
        .clear()
        .type("Updated description")
        .should("have.value", "Updated description");
      cy.getByTestId("submit-btn").click();
      cy.wait("@updateOrganization").then((interception) => {
        const { body } = interception.request;
        expect(body.fides_key).to.eq("default_organization");
        expect(body.description).to.eq("Updated description");
      });
    });
  });

  describe("AWS scan steps", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();

      // Move past organization step.
      cy.getByTestId("organization-info-form");
      cy.getByTestId("submit-btn").click();
      // Select AWS to move to form step.
      cy.getByTestId("add-system-form");
      cy.getByTestId("aws-btn").click();
      // Fill form
      cy.getByTestId("authenticate-aws-form");
      cy.getByTestId("input-aws_access_key_id").type("fakeAccessKey");
      cy.getByTestId("input-aws_secret_access_key").type("fakeSecretAccessKey");
      cy.getByTestId("input-region_name").type("us-east-1{Enter}");
    });

    it("Allows submitting the form and reviewing the results", () => {
      cy.intercept("POST", "/api/v1/generate", {
        fixture: "generate/system.json",
      }).as("postGenerate");

      cy.getByTestId("submit-btn").click();
      cy.wait("@postGenerate");

      cy.getByTestId("scan-results");
      cy.getByTestId(`checkbox-example-system-1`).click();
      cy.getByTestId("register-btn").click();

      // The request while editing the form should match the generated system's body.
      cy.intercept("POST", "/api/v1/system", {
        fixture: "generate/system_to_review.json",
      }).as("postSystem");
      cy.intercept("PUT", "/api/v1/system*", {
        fixture: "generate/system_to_review.json",
      }).as("putSystem");

      // The form interactions are covered by the system forms tests.
      cy.contains("Continue").click();
      cy.getByTestId("confirm-btn").click();
      cy.getByTestId("privacy-declaration-form");
      cy.getByTestId("input-name").type("declaration");
      cy.getByTestId("input-data_categories").click().type(`user{enter}`);
      cy.getByTestId("input-data_use")
        .click()
        .contains("advertising.first_party")
        .click();
      cy.getByTestId("input-data_subjects").type(`user{enter}`);
      cy.getByTestId("add-btn").click();
      cy.getByTestId("next-btn").click();
      cy.getByTestId("confirm-btn").click();

      // Just the first system is reviewed.
      cy.get(`[data-testid="system-reviewed"]`).should("have.length", 1);
      cy.get(`[data-testid="system-needs-review"]`).should("have.length", 2);
    });

    it("Displays API errors and allows resubmission", () => {
      cy.intercept("POST", "/api/v1/generate", {
        statusCode: 403,
        body: {
          detail: "The security token included in the request is invalid.",
        },
      }).as("postGenerate403");
      cy.getByTestId("submit-btn").click();
      cy.wait("@postGenerate403");
      // Expect the custom message for this specific error.
      cy.getByTestId("scanner-error");
      cy.getByTestId("permission-msg");

      cy.intercept("POST", "/api/v1/generate", {
        statusCode: 500,
        body: "Internal Server Error",
      }).as("postGenerate500");
      cy.getByTestId("submit-btn").click();
      cy.wait("@postGenerate500");
      // Expect the generic message with a log.
      cy.getByTestId("scanner-error");
      cy.getByTestId("generic-msg");
      cy.getByTestId("error-log").contains("Internal Server Error");
    });

    it("Allows stepping back to the previous step during an in-progress scan", () => {
      cy.intercept(
        "POST",
        "/api/v1/generate",

        (req) => {
          req.continue((res) => {
            res.setDelay(1000);
          });
        }
      ).as("postGenerate");
      cy.getByTestId("submit-btn")
        .click()
        .then(() => {
          cy.getByTestId("close-scan-in-progress").click();
          cy.contains("Cancel Scan!");
          cy.contains("Yes, Cancel").click();
          cy.contains("Scan for Systems");
        });
    });
  });
});
