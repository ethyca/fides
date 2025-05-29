import { stubPlus, stubTaxonomyEntities } from "cypress/support/stubs";

declare global {
  namespace Cypress {
    interface Chainable {
      attachFile(options: {
        fileContent: string;
        fileName: string;
        mimeType: string;
      }): Chainable<JQuery<HTMLElement>>;
    }
  }
}

describe("Shared Monitor Configuration", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubTaxonomyEntities();
  });

  describe("Create new configuration", () => {
    beforeEach(() => {
      cy.intercept("POST", "/api/v1/plus/shared-monitor-config", {
        statusCode: 200,
        body: {
          id: "test-config-1",
          name: "Test Config",
          description: "Test description",
          classify_params: {
            context_regex_pattern_mapping: [
              ["test-regex", "user.contact.email"],
            ],
          },
        },
      }).as("createConfig");
    });

    // TODO: tests broken

    it("should create a new configuration", () => {
      cy.visit("/integrations");
      cy.getByTestId("configurations-btn").click();

      cy.getByTestId("create-new-btn").click();

      // Fill in the form
      cy.getByTestId("input-name").type("Test Config");
      cy.getByTestId("input-description").type("Test description");

      // Add a rule
      cy.getByTestId("input-rules.0.regex").type("test-regex");
      cy.getByTestId("input-rules.0.dataCategory").antSelect("user");

      // Submit the form
      cy.getByTestId("save-btn").click({ force: true });

      // Verify the API call
      cy.wait("@createConfig").then((interception) => {
        expect(interception.request.body).to.deep.equal({
          name: "Test Config",
          description: "Test description",
          classify_params: {
            context_regex_pattern_mapping: [["test-regex", "user"]],
          },
        });
      });
    });

    it("should validate required fields", () => {
      cy.visit("/integrations");
      cy.getByTestId("configurations-btn").click();

      cy.getByTestId("create-new-btn").click();

      // Try to submit without filling required fields
      cy.getByTestId("save-btn").click();

      // Check for validation messages
      cy.getByTestId("form-item-name").should(
        "contain",
        "Config name is required",
      );
      cy.getByTestId("form-item-rules.0.regex").should(
        "contain",
        "Regex is required",
      );
      cy.getByTestId("form-item-rules.0.dataCategory").should(
        "contain",
        "Data category is required",
      );
    });

    it.only("should allow adding multiple rules", () => {
      cy.visit("/integrations");
      cy.getByTestId("configurations-btn").click();

      cy.getByTestId("create-new-btn").click();

      // Fill in first rule
      cy.getByTestId("input-name").type("Test Config");
      cy.getByTestId("input-rules.0.regex").type("test-regex-1");
      cy.getByTestId("input-rules.0.dataCategory").antSelect("system");

      // Add second rule
      cy.getByTestId("add-rule-btn").click();
      cy.getByTestId("input-rules.1.regex").type("test-regex-2");
      cy.getByTestId("input-rules.1.dataCategory").antSelect("user");

      // Submit the form
      cy.getByTestId("save-btn").click();

      // Verify the API call
      cy.wait("@createConfig").then((interception) => {
        expect(
          interception.request.body.classify_params
            .context_regex_pattern_mapping,
        ).to.deep.equal([
          ["test-regex-1", "system"],
          ["test-regex-2", "user"],
        ]);
      });
    });

    it("should allow uploading rules via CSV", () => {
      cy.visit("/integrations");
      cy.getByTestId("configurations-btn").click();

      // Create a CSV file with rules
      const csvContent =
        "test-regex-1,user.contact.email\ntest-regex-2,user.contact.phone";
      const blob = new Blob([csvContent], { type: "text/csv" });
      const file = new File([blob], "rules.csv", { type: "text/csv" });

      // Upload the file
      cy.getByTestId("upload-csv").attachFile({
        fileContent: csvContent,
        fileName: "rules.csv",
        mimeType: "text/csv",
      });

      // Verify the rules were imported
      cy.getByTestId("input-rules.0.regex").should(
        "have.value",
        "test-regex-1",
      );
      cy.getByTestId("input-rules.0.dataCategory").should(
        "have.value",
        "user.contact.email",
      );
      cy.getByTestId("input-rules.1.regex").should(
        "have.value",
        "test-regex-2",
      );
      cy.getByTestId("input-rules.1.dataCategory").should(
        "have.value",
        "user.contact.phone",
      );
    });
  });

  describe("Edit existing configuration", () => {
    const configId = "test-config-1";

    beforeEach(() => {
      cy.intercept("GET", `/api/v1/plus/shared-monitor-config/${configId}`, {
        statusCode: 200,
        body: {
          id: configId,
          name: "Test Config",
          description: "Test description",
          classify_params: {
            context_regex_pattern_mapping: [
              ["test-regex", "user.contact.email"],
            ],
          },
        },
      }).as("getConfig");

      cy.intercept("PUT", `/api/v1/plus/shared-monitor-config/${configId}`, {
        statusCode: 200,
        body: {
          id: configId,
          name: "Updated Config",
          description: "Updated description",
          classify_params: {
            context_regex_pattern_mapping: [
              ["updated-regex", "user.contact.email"],
            ],
          },
        },
      }).as("updateConfig");
    });

    it("should load and edit existing configuration", () => {
      cy.visit("/integrations");
      cy.getByTestId("configurations-btn").click();
      cy.getByTestId(`config-${configId}`).click();

      // Verify initial values
      cy.getByTestId("input-name").should("have.value", "Test Config");
      cy.getByTestId("input-description").should(
        "have.value",
        "Test description",
      );
      cy.getByTestId("input-rules.0.regex").should("have.value", "test-regex");
      cy.getByTestId("input-rules.0.dataCategory").should(
        "have.value",
        "user.contact.email",
      );

      // Update values
      cy.getByTestId("input-name").clear().type("Updated Config");
      cy.getByTestId("input-description").clear().type("Updated description");
      cy.getByTestId("input-rules.0.regex").clear().type("updated-regex");

      // Submit the form
      cy.getByTestId("save-btn").click();

      // Verify the API call
      cy.wait("@updateConfig").then((interception) => {
        expect(interception.request.body).to.deep.equal({
          name: "Updated Config",
          description: "Updated description",
          classify_params: {
            context_regex_pattern_mapping: [
              ["updated-regex", "user.contact.email"],
            ],
          },
        });
      });
    });

    it("should allow removing rules", () => {
      cy.visit("/integrations");
      cy.getByTestId("configurations-btn").click();
      cy.getByTestId(`config-${configId}`).click();

      // Add a second rule
      cy.getByTestId("add-rule-btn").click();
      cy.getByTestId("input-rules.1.regex").type("test-regex-2");
      cy.getByTestId("input-rules.1.dataCategory").type("user.contact.phone");

      // Remove the first rule
      cy.getByTestId("remove-rule-0").click();

      // Submit the form
      cy.getByTestId("save-btn").click();

      // Verify the API call
      cy.wait("@updateConfig").then((interception) => {
        expect(
          interception.request.body.classify_params
            .context_regex_pattern_mapping,
        ).to.deep.equal([["test-regex-2", "user.contact.phone"]]);
      });
    });
  });
});
