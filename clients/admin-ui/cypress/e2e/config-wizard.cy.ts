describe("Config Wizard", () => {
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

    it("Allows submitting the form and viewing the results", () => {
      cy.intercept("POST", "/api/v1/generate", {
        fixture: "generate/system.json",
      }).as("postGenerate");

      cy.getByTestId("submit-btn").click();
      cy.wait("@postGenerate");

      cy.getByTestId("scan-results-form");
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
  });
});
