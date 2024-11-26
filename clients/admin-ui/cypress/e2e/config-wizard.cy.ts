import { stubSystemCrud, stubTaxonomyEntities } from "cypress/support/stubs";

import { ADD_SYSTEMS_ROUTE } from "~/features/common/nav/v2/routes";

describe("Config Wizard", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/organization/*", {
      fixture: "organizations/default_organization.json",
    }).as("getOrganization");
  });

  describe("AWS scan steps", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();

      cy.visit(ADD_SYSTEMS_ROUTE);
      // Select AWS to move to form step.
      cy.getByTestId("add-systems");
      cy.getByTestId("aws-btn").click();
      // Fill form
      cy.getByTestId("authenticate-aws-form");
      cy.getByTestId("input-aws_access_key_id").type("fakeAccessKey");
      cy.getByTestId("input-aws_secret_access_key").type("fakeSecretAccessKey");
      cy.getByTestId("controlled-select-region_name").type("us-east-1{Enter}");
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
      cy.intercept("POST", "/api/v1/generate", {
        delay: 1000,
        statusCode: 503,
      }).as("postGenerateDelayedAndCanceled");
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

      cy.visit(ADD_SYSTEMS_ROUTE);
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
