import {
  stubDatamap,
  stubPlus,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { ResourceTypes } from "~/types/api";

describe("Taxonomy management with Plus features", () => {
  beforeEach(() => {
    cy.login();
    stubTaxonomyEntities();
    stubPlus(true);
    stubDatamap();
    cy.visit("/taxonomy");
  });

  const RESOURCE_TYPE = {
    label: "Data Categories",
    key: ResourceTypes.DATA_CATEGORY,
  };
  const RESOURCE_PARENT = {
    label: "User Data",
    key: "user",
  };
  const RESOURCE_CHILD = {
    label: "Job Title",
    key: "user.job_title",
  };

  const navigateToEditor = () => {
    cy.getByTestId(`accordion-item-${RESOURCE_PARENT.label}`).click();
    cy.getByTestId(`item-${RESOURCE_CHILD.label}`).click({ force: true });
    cy.getByTestId("edit-btn").click();
  };

  // TODO: Inputs are no longer created on this screen.
  // This should eventually be migrated to the custom fields tests
  describe.skip("Defining custom lists", () => {
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

  // TODO: Inputs are no longer created on this screen.
  // This should eventually be migrated to the custom fields tests
  describe.skip("Defining custom fields", () => {
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
        },
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
        },
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
        cy.selectOption("input-field_type", "Multiple select");
        cy.selectOption("input-allow_list_id", "Prime numbers");
      });

      cy.intercept(
        "POST",
        "/api/v1/plus/custom-metadata/custom-field-definition",
        {
          fixture:
            "taxonomy/custom-metadata/custom-field-definition/create.json",
        },
      ).as("createCustomField");

      cy.getByTestId("custom-fields-modal-submit-btn").click();

      cy.wait("@createCustomField").its("request.body").should("include", {
        active: true,
        field_type: "string[]",
        name: "Multi-select",
        resource_type: RESOURCE_TYPE.key,
      });
    });

    it("validates required form fields", () => {
      cy.getByTestId("custom-fields-modal-submit-btn").click();
      cy.getByTestId("create-custom-fields-form").should(
        "contain",
        "Name is required",
      );
    });
  });

  describe("Using custom fields", () => {
    beforeEach(() => {
      cy.intercept(
        {
          method: "GET",
          pathname: "/api/v1/plus/custom-metadata/allow-list",
          query: {
            show_values: "true",
          },
        },
        {
          fixture: "taxonomy/custom-metadata/allow-list/list.json",
        },
      ).as("getAllowLists");
      cy.intercept(
        "GET",
        // Cypress route matching doesn't escape special characters (whitespace).
        `/api/v1/plus/custom-metadata/custom-field-definition/resource-type/${encodeURIComponent(
          RESOURCE_TYPE.key,
        )}`,

        {
          fixture: "taxonomy/custom-metadata/custom-field-definition/list.json",
        },
      ).as("getCustomFieldDefinitions");
      cy.intercept(
        "GET",
        `/api/v1/plus/custom-metadata/custom-field/resource/${RESOURCE_CHILD.key}`,
        {
          fixture: "taxonomy/custom-metadata/custom-field/list.json",
        },
      ).as("getCustomFields");

      navigateToEditor();

      cy.wait([
        "@getAllowLists",
        "@getCustomFieldDefinitions",
        "@getCustomFields",
      ]);
    });

    const testIdSingle =
      "input-customFieldValues.id-custom-field-definition-starter-pokemon";
    const testIdMulti =
      "input-customFieldValues.id-custom-field-definition-pokemon-party";

    it("initializes form fields with values returned by the API", () => {
      cy.getByTestId("custom-fields-list");
      cy.getSelectValueContainer(testIdSingle).contains("Squirtle");

      ["Charmander", "Eevee", "Snorlax"].forEach((value) => {
        cy.getSelectValueContainer(testIdMulti).contains(value);
      });
    });

    it("allows choosing and changing selections", () => {
      cy.getByTestId("custom-fields-list");

      cy.clearSingleValue(testIdSingle);
      cy.selectOption(testIdSingle, "Snorlax");
      cy.getSelectValueContainer(testIdSingle).contains("Snorlax");
      cy.clearSingleValue(testIdSingle);

      cy.removeMultiValue(testIdMulti, "Eevee");
      cy.removeMultiValue(testIdMulti, "Snorlax");

      // clicking directly on the select element as we usually do hits the
      // "remove" on the Charmander tag, so force it to find the dropdown
      // indicator instead
      cy.getByTestId(testIdMulti)
        .find(".custom-select__dropdown-indicator")
        .click();
      cy.getByTestId(testIdMulti)
        .find(".custom-select__menu-list")
        .contains("Eevee")
        .click();

      ["Charmander", "Eevee"].forEach((value) => {
        cy.getSelectValueContainer(testIdMulti).contains(value);
      });

      cy.intercept("POST", `/api/v1/plus/custom-metadata/custom-field/bulk`, {
        body: {},
      }).as("bulkUpdateCustomField");

      cy.getByTestId("submit-btn").click();

      cy.wait("@bulkUpdateCustomField").then((interception) => {
        const { body } = interception.request;
        expect(body.resource_id).to.eql(RESOURCE_CHILD.key);
        expect(body.delete).to.eql(["id-custom-field-starter-pokemon"]);
        expect(body.upsert).to.eql([
          {
            custom_field_definition_id:
              "id-custom-field-definition-pokemon-party",
            resource_id: "user.job_title",
            id: "id-custom-field-pokemon-party",
            value: ["Charmander", "Eevee"],
          },
        ]);
      });
    });
  });
});
