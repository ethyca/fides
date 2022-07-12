describe("Config Wizard", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/organization/*", {
      fixture: "organization.json",
    }).as("getOrganization");

    cy.intercept("PUT", "/api/v1/organization**", {
      fixture: "organization.json",
    }).as("updateOrganization");

    cy.intercept("POST", "/api/v1/generate", {
      fixture: "generate_system.json",
    }).as("postGenerate");
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
    });

    it("Allows submitting the form and viewing the results", () => {
      cy.getByTestId("authenticate-aws-form");
      cy.getByTestId("input-aws_access_key_id").type("fake-access-key");
      cy.getByTestId("input-aws_secret_access_key").type(
        "fake-secret-access-key"
      );
      cy.getByTestId("input-region_name").type("us-east-1{Enter}");
      cy.getByTestId("submit-btn").click();

      cy.wait("@postGenerate");
      cy.getByTestId("scan-results-form");
    });
  });
});
