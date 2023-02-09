import { stubPlus, stubTaxonomyEntities } from "cypress/support/stubs";

describe("Taxonomy management with Plus features", () => {
  beforeEach(() => {
    cy.login();
    stubTaxonomyEntities();
    stubPlus(true);
    cy.visit("/taxonomy");
  });

  describe("Defining custom lists", () => {
    beforeEach(() => {
      cy.getByTestId("accordion-item-User Data").click();
      cy.getByTestId("item-Biometric Data")
        .click()
        .within(() => {
          cy.getByTestId("edit-btn").click();
        });
      cy.getByTestId("add-custom-field-btn").click();
      cy.getByTestId("tab-Create custom lists").click();
    });

    it("can create a list", () => {
      const listValues = ["such", "metadata", "so", "custom"];

      cy.getByTestId("create-custom-lists-form").within(() => {
        cy.getByTestId("custom-input-name").type("Custom list");

        listValues.forEach((value, index) => {
          cy.getByTestId("add-list-value-btn").click();
          cy.getByTestId(`custom-input-allowed_values[${index}]`).type(value);
        });

        // Loop above adds an extra blank input, so remove it while also testing the button.
        cy.getByTestIdPrefix("remove-list-value-btn").last().click();
      });

      cy.intercept("PUT", "/api/v1/plus/custom-metadata/allow-list", {
        fixture: "taxonomy/custom-metadata/allow-list/create.json",
      }).as("createAllowList");

      cy.getByTestId("custom-fields-modal-submit-btn").click();

      cy.wait("@createAllowList").its("request.body").should("eql", {
        name: "Custom list",
        allowed_values: listValues,
      });
    });

    it("validates required fields", () => {
      cy.getByTestId("custom-fields-modal-submit-btn").click();
      cy.getByTestId("create-custom-lists-form")
        .should("contain", "Name is required")
        .should("contain", "List item is required");
    });
  });
});
