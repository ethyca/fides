import { stubSystemCrud, stubTaxonomyEntities } from "cypress/support/stubs";

describe("Config Wizard", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/organization/*", {
      fixture: "organization.json",
    }).as("getOrganization");
  });

  // TODO: Update Cypress test to reflect the nav bar 2.0
  describe.skip("Organization setup", () => {
    beforeEach(() => {
      cy.intercept("PUT", "/api/v1/organization**", {
        fixture: "organization.json",
      }).as("updateOrganization");
    });

    it("Can fill in an organization", () => {
      cy.fixture("organization.json").then((org) => {
        cy.intercept("GET", "/api/v1/organization/*", {
          body: { org, name: null, description: null },
        }).as("getEmptyOrganization");
      });
      cy.visit("/add-systems");
      cy.getByTestId("guided-setup-btn").click();
      cy.wait("@getEmptyOrganization");

      cy.getByTestId("organization-info-form");
      cy.getByTestId("input-name").type("Updated name");
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
      cy.getByTestId("add-systems");
    });

    it("Can skip the org flow if an organization already exists", () => {
      cy.visit("/add-systems");
      cy.getByTestId("guided-setup-btn").click();
      cy.getByTestId("add-systems");
    });
  });

  describe("AWS scan steps", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();

      cy.visit("/add-systems");
      // Select AWS to move to form step.
      cy.getByTestId("add-systems");
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

      // assert that the systems do POST
      cy.intercept("POST", "/api/v1/system/upsert", []).as("upsertSystems");

      cy.getByTestId("warning-modal-confirm-btn").click();

      cy.wait("@upsertSystems").then((interception) => {
        assert.isNotNull(interception.response.body, "Upsert call has data");
      });
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
          cy.getByTestId("add-systems");
        });
    });
  });
  describe("Okta scan steps", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();

      cy.visit("/add-systems");
      // Select Okta to move to form step.
      cy.getByTestId("add-systems");
      cy.getByTestId("okta-btn").click();
      // Fill form
      cy.getByTestId("authenticate-okta-form");
      cy.getByTestId("input-orgUrl").type("https://ethyca.com/");
      cy.getByTestId("input-token").type("fakeToken");
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

      // assert that the systems do POST
      cy.intercept("POST", "/api/v1/system/upsert", []).as("upsertSystems");

      cy.getByTestId("warning-modal-confirm-btn").click();

      cy.wait("@upsertSystems").then((interception) => {
        assert.isNotNull(interception.response.body, "Upsert call has data");
      });
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
      // Expect the general message with a log.
      cy.getByTestId("scanner-error");
      cy.getByTestId("generic-msg");

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
