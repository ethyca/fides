import { stubPlus, stubTaxonomyEntities } from "cypress/support/stubs";

import { ResourceTypes } from "~/types/api";

describe("Taxonomy management with Plus features", () => {
  beforeEach(() => {
    cy.login();
    stubTaxonomyEntities();
    stubPlus(true);
    cy.visit("/taxonomy");
  });

  const navigateToEditor = () => {
    cy.getByTestId("accordion-item-User Data").click();
    cy.getByTestId("item-Biometric Data")
      .click()
      .within(() => {
        cy.getByTestId("edit-btn").click();
      });
  };

  const selectOption = (selectorId: string, optionText: string) => {
    cy.getByTestId(selectorId)
      .click()
      .within(() => {
        cy.contains(optionText).click();
      });
  };

  describe("Defining custom lists", () => {
    beforeEach(() => {
      navigateToEditor();
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

    it("validates required form fields", () => {
      cy.getByTestId("custom-fields-modal-submit-btn").click();
      cy.getByTestId("create-custom-lists-form")
        .should("contain", "Name is required")
        .should("contain", "List item is required");
    });
  });

  describe("Defining custom fields", () => {
    beforeEach(() => {
      cy.intercept(
        {
          method: "GET",
          pathname: "/api/v1/plus/custom-metadata/allow-list",
          query: {
            show_values: "false",
          },
        },
        {
          fixture: "taxonomy/custom-metadata/allow-list/list.json",
        }
      ).as("getAllowLists");

      navigateToEditor();
      cy.getByTestId("add-custom-field-btn").click();
      cy.getByTestId("tab-Create custom fields").click();

      cy.wait("@getAllowLists");
    });

    it("can create a single-select custom field", () => {
      cy.getByTestId("create-custom-fields-form").within(() => {
        cy.getByTestId("custom-input-name").type("Single-select");
      });

      cy.intercept(
        "POST",
        "/api/v1/plus/custom-metadata/custom-field-definition",
        {
          fixture:
            "taxonomy/custom-metadata/custom-field-definition/create.json",
        }
      ).as("createCustomField");

      cy.getByTestId("custom-fields-modal-submit-btn").click();

      cy.wait("@createCustomField").its("request.body").should("include", {
        active: true,
        field_type: "string",
        name: "Single-select",
        resource_type: ResourceTypes.DATA_CATEGORY,
      });
    });

    it("can create a multi-select custom field", () => {
      cy.getByTestId("create-custom-fields-form").within(() => {
        cy.getByTestId("custom-input-name").type("Multi-select");
        selectOption("input-field_type", "Multiple select");
        selectOption("input-allow_list_id", "Prime numbers");
      });

      cy.intercept(
        "POST",
        "/api/v1/plus/custom-metadata/custom-field-definition",
        {
          fixture:
            "taxonomy/custom-metadata/custom-field-definition/create.json",
        }
      ).as("createCustomField");

      cy.getByTestId("custom-fields-modal-submit-btn").click();

      cy.wait("@createCustomField").its("request.body").should("include", {
        active: true,
        field_type: "string[]",
        name: "Multi-select",
        resource_type: ResourceTypes.DATA_CATEGORY,
      });
    });

    it("validates required form fields", () => {
      cy.getByTestId("custom-fields-modal-submit-btn").click();
      cy.getByTestId("create-custom-fields-form").should(
        "contain",
        "Name is required"
      );
    });
  });
});
