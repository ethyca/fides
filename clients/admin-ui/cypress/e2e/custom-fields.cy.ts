import { stubCustomFields, stubPlus } from "cypress/support/stubs";

import { LegacyResourceTypes } from "~/features/common/custom-fields";
import {
  RESOURCE_TYPE_MAP,
  VALUE_TYPE_RESOURCE_TYPE_MAP,
} from "~/features/custom-fields/constants";
import { TaxonomyTypeEnum } from "~/features/taxonomy/constants";
import { RoleRegistryEnum } from "~/types/api";

describe("Custom Fields V2", () => {
  beforeEach(() => {
    stubPlus(true);
    stubCustomFields();
    cy.login();
    cy.visit("/settings/custom-fields");
  });

  describe("Custom Fields Table", () => {
    it("displays the custom fields table with correct columns", () => {
      cy.getByTestId("custom-fields-management").should("exist");
      cy.get(".ant-table-thead").within(() => {
        cy.contains("Name").should("exist");
        cy.contains("Description").should("exist");
        cy.contains("Type").should("exist");
        cy.contains("Applies to").should("exist");
        cy.contains("Enabled").should("exist");
        cy.contains("Actions").should("exist");
      });
    });

    it("navigates to create form when Add custom field is clicked", () => {
      cy.getByTestId("add-custom-field-btn").click();
      cy.url().should("include", "/settings/custom-fields/new");
    });
  });

  describe("Custom Field Form", () => {
    beforeEach(() => {
      cy.visit("/settings/custom-fields/new");
    });

    it("displays all required form fields", () => {
      cy.get("form").within(() => {
        cy.getByTestId("input-name").should("exist");
        cy.getByTestId("input-description").should("exist");
        cy.getByTestId("select-template").should("exist");
        cy.getByTestId("select-value-type").should("exist").should("be.hidden");
        cy.getByTestId("select-resource-type").should("exist");
      });
    });

    it("allows selecting a taxonomy type", () => {
      cy.getByTestId("select-template").antSelect("Data categories");
      cy.getByTestId("input-name").type("Test taxonomy field");
      cy.getByTestId("select-value-type")
        .should("be.hidden")
        .should("contain", "Data categories");
      cy.getByTestId("select-field-type").should("not.exist");
    });

    it("filters location options when taxonomy type is selected", () => {
      // First, check available locations before selecting taxonomy
      cy.getByTestId("select-resource-type").click();
      cy.get(".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
        .should("be.visible")
        .then(($dropdown) => {
          const initialOptions = $dropdown.find(
            ".ant-select-item-option",
          ).length;
          cy.get("body").click(0, 0); // Close dropdown

          // Select a taxonomy type
          cy.getByTestId("select-template").antSelect("Data categories");

          // Check that "taxonomy:data category" is filtered out from location options
          cy.getByTestId("select-resource-type").click();
          cy.get(".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
            .should("be.visible")
            .within(() => {
              // Should not contain the matching taxonomy location
              cy.contains("taxonomy:data category").should("not.exist");
              // Should still contain other locations
              cy.contains("system:information").should("exist");
            });
        });
    });

    it("allows switching between Custom and Taxonomy templates", () => {
      cy.getByTestId("input-name").type("Test field");

      // Start with Custom template
      cy.getByTestId("select-template").antSelect("Custom");
      cy.getByTestId("select-field-type").should("exist");

      // Switch to Taxonomy template
      cy.getByTestId("select-template").antSelect("Data categories");
      cy.getByTestId("select-field-type").should("not.exist");
      cy.getByTestId("select-value-type")
        .should("be.hidden")
        .should("contain", "Data categories");

      // Switch back to Custom
      cy.getByTestId("select-template").antSelect("Custom");
      cy.getByTestId("select-field-type").should("exist");
    });

    it("validates required fields", () => {
      cy.getByTestId("save-btn").click();
      cy.contains("Please enter a name").should("be.visible");
      cy.contains("Please select a location").should("be.visible");

      cy.getByTestId("input-name").type("custom name");
      cy.getByTestId("save-btn").click();
      cy.getByTestId("select-template").antSelect("Custom");
      cy.getByTestId("save-btn").click();
      cy.contains("Please select a field type").should("be.visible");
      cy.getByTestId("select-field-type").antSelect("Single select");
      cy.getByTestId("save-btn").click();
      cy.contains("At least one option is required for selects").should(
        "be.visible",
      );
    });

    it("shows options field for select types", () => {
      cy.getByTestId("input-name").type("custom name");
      // Select Custom template first
      cy.getByTestId("select-template").antSelect("Custom");
      cy.getByTestId("select-field-type").antSelect("Single select");

      // Add and validate options
      cy.getByTestId("add-option-btn").click();
      cy.getByTestId("add-option-btn").click();

      // Check if options section appears
      cy.contains("Options").should("be.visible");
      cy.getByTestId("input-option-0").should("exist");
      cy.getByTestId("input-option-1").should("exist");
    });

    it("validates unique options for select types", () => {
      cy.getByTestId("input-name").type("custom name");
      // Select Custom template first
      cy.getByTestId("select-template").antSelect("Custom");
      cy.getByTestId("select-field-type").antSelect("Single select");

      // Add duplicate options
      cy.getByTestId("add-option-btn").click();
      cy.getByTestId("input-option-0").type("Option 1");
      cy.getByTestId("add-option-btn").click();
      cy.getByTestId("input-option-1").type("Option 1").blur();

      // Check for duplicate validation error
      cy.contains("Option values must be unique").should("be.visible");
    });

    it("successfully creates a custom field", () => {
      const fieldName = "Test Field";
      const fieldDesc = "Test Description";

      cy.getByTestId("input-name").type(fieldName).blur();
      cy.getByTestId("input-description").type(fieldDesc);
      cy.getByTestId("select-template").antSelect("Custom");
      cy.getByTestId("select-field-type").antSelect("Single select");
      cy.getByTestId("add-option-btn").click();
      cy.getByTestId("input-option-0").type("Option 1");
      cy.getByTestId("select-resource-type").antSelect("system:information");
      cy.getByTestId("save-btn").click();
      cy.wait("@createCustomFieldDefinition")
        .its("response.statusCode")
        .should("eq", 201);
      cy.wait("@upsertAllowList").its("response.statusCode").should("eq", 200);
      cy.url().should("not.include", "/new");
    });
  });

  describe("Custom Field Edit", () => {
    it("loads existing field data for editing", () => {
      cy.visit("/settings/custom-fields");
      cy.getByTestId("edit-btn").first().click();

      // Verify form is populated
      cy.getByTestId("input-name").should("have.value", "Test Custom Field");
      cy.getByTestId("select-resource-type").should("exist");
      cy.getByTestId("select-field-type").should("exist");
    });

    it("disables resource type select when editing existing field", () => {
      cy.visit("/settings/custom-fields");
      cy.getByTestId("edit-btn").first().click();

      // Verify resource type is disabled
      cy.getByTestId("select-resource-type").should(
        "have.class",
        "ant-select-disabled",
      );
    });

    it("navigates to edit form when name link is clicked", () => {
      cy.visit("/settings/custom-fields");
      cy.get(".ant-table-tbody").within(() => {
        cy.get("a").first().click();
      });
      cy.url().should("include", "/settings/custom-fields/");
      cy.getByTestId("input-name").should("exist");
    });

    it("allows updating field properties", () => {
      cy.visit("/settings/custom-fields");
      cy.getByTestId("edit-btn").first().click();

      // Update name
      cy.getByTestId("input-name").clear().type("Updated field name");
      cy.getByTestId("select-template").should("contain", "Custom");
      cy.getByTestId("add-option-btn").click();
      cy.getByTestId("input-option-3").type("Added option");

      cy.getByTestId("save-btn").click();
      cy.wait("@updateCustomFieldDefinition")
        .its("response.statusCode")
        .should("eq", 200);
      cy.wait("@upsertAllowList").its("response.statusCode").should("eq", 200);
      cy.url().should("not.contain", "/settings/custom-fields/");
    });

    it("shows delete button for users with delete permission", () => {
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.visit("/settings/custom-fields");
      cy.getByTestId("edit-btn").first().click();

      // Verify delete button is present
      cy.getByTestId("delete-btn").should("exist");
    });

    it("does not show edit button for users without delete permission", () => {
      cy.assumeRole(RoleRegistryEnum.VIEWER);
      cy.visit("/settings/custom-fields");
      cy.getByTestId("edit-btn").should("not.exist");
    });

    it("confirms before deleting a custom field", () => {
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.visit("/settings/custom-fields");
      cy.getByTestId("edit-btn").first().click();

      // Click delete and verify modal
      cy.getByTestId("delete-btn").click();
      cy.contains("Are you sure you want to delete").should("be.visible");

      // Confirm deletion
      cy.get(".ant-modal-confirm-btns").within(() => {
        cy.contains("Delete").click();
      });
      cy.wait("@deleteCustomFieldDefinition")
        .its("response.statusCode")
        .should("eq", 204);
      cy.contains("Custom field deleted successfully").should("be.visible");
      cy.url().should("not.include", "/edit");
    });
  });
});
