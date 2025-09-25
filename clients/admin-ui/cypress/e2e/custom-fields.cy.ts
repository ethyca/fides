import { stubCustomFields, stubPlus } from "cypress/support/stubs";

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
        cy.getByTestId("select-resource-type").should("exist");
        cy.getByTestId("select-field-type").should("exist");
      });
    });

    it("validates required fields", () => {
      cy.getByTestId("save-btn").click();
      cy.contains("Please enter a name").should("be.visible");
      cy.contains("Please select a resource type").should("be.visible");
      cy.contains("Please select a field type").should("be.visible");
    });

    it("shows options field for select types", () => {
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
      // Select single select type
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

      cy.getByTestId("input-name").type(fieldName);
      cy.getByTestId("input-description").type(fieldDesc);
      cy.getByTestId("select-resource-type").antSelect("system:information");
      cy.getByTestId("select-field-type").antSelect("Single select");
      cy.getByTestId("add-option-btn").click();
      cy.getByTestId("input-option-0").type("Option 1");
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
      // Assuming we have a custom field with ID "test-id"
      cy.visit("/settings/custom-fields");
      cy.getByTestId("edit-btn").first().click();

      // Verify form is populated
      cy.getByTestId("input-name").should("have.value", "Test Custom Field");
      cy.getByTestId("select-resource-type").should("exist");
      cy.getByTestId("select-field-type").should("exist");
    });

    it("allows updating field properties", () => {
      cy.visit("/settings/custom-fields");
      cy.getByTestId("edit-btn").first().click();

      // Update name
      cy.getByTestId("input-name").clear().type("Updated field name");
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
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteCustomFieldDefinition")
        .its("response.statusCode")
        .should("eq", 204);
      cy.contains("Custom field deleted successfully").should("be.visible");
      cy.url().should("not.include", "/edit");
    });
  });
});
