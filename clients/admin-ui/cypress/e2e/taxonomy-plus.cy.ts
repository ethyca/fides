import { stubPlus, stubTaxonomyEntities } from "cypress/support/stubs";

import { ResourceTypes } from "~/types/api";

describe("Taxonomy management with Plus features", () => {
  beforeEach(() => {
    cy.login();
    stubTaxonomyEntities();
    stubPlus(true);
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
    label: "Biometric Data",
    key: "user.biometric",
  };

  const navigateToEditor = () => {
    cy.getByTestId(`accordion-item-${RESOURCE_PARENT.label}`).click();
    cy.getByTestId(`item-${RESOURCE_CHILD.label}`)
      .click()
      .within(() => {
        cy.getByTestId("edit-btn").click();
      });
  };

  // TODO: Extract these to a cypress support file.
  const getSelectValueContainer = (selectorId: string) =>
    cy.getByTestId(selectorId).find(`.custom-select__value-container`);

  const getSelectOptionList = (selectorId: string) =>
    cy.getByTestId(selectorId).click().find(`.custom-select__menu-list`);

  const selectOption = (selectorId: string, optionText: string) => {
    getSelectOptionList(selectorId).contains(optionText).click();
  };

  const removeMultiValue = (selectorId: string, optionText: string) =>
    getSelectValueContainer(selectorId)
      .contains(optionText)
      .siblings(".custom-select__multi-value__remove")
      .click();

  const clearSingleValue = (selectorId: string) =>
    cy.getByTestId(selectorId).find(".custom-select__clear-indicator").click();

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
        resource_type: RESOURCE_TYPE.key,
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
        }
      ).as("getAllowLists");
      cy.intercept(
        "GET",
        // Cypress route matching doesn't escape special characters (whitespace).
        `/api/v1/plus/custom-metadata/custom-field-definition/resource-type/${encodeURIComponent(
          RESOURCE_TYPE.key
        )}`,

        {
          fixture: "taxonomy/custom-metadata/custom-field-definition/list.json",
        }
      ).as("getCustomFieldDefinitions");
      cy.intercept(
        "GET",
        `/api/v1/plus/custom-metadata/custom-field/resource/${RESOURCE_CHILD.key}`,
        {
          fixture: "taxonomy/custom-metadata/custom-field/list.json",
        }
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
      getSelectValueContainer(testIdSingle).contains("Squirtle");

      ["Charmander", "Eevee", "Snorlax"].forEach((value) => {
        getSelectValueContainer(testIdMulti).contains(value);
      });
    });

    it("allows choosing and changing selections", () => {
      cy.getByTestId("custom-fields-list");

      clearSingleValue(testIdSingle);
      selectOption(testIdSingle, "Snorlax");
      getSelectValueContainer(testIdSingle).contains("Snorlax");
      clearSingleValue(testIdSingle);

      removeMultiValue(testIdMulti, "Eevee");
      removeMultiValue(testIdMulti, "Snorlax");
      selectOption(testIdMulti, "Eevee");

      ["Charmander", "Eevee"].forEach((value) => {
        getSelectValueContainer(testIdMulti).contains(value);
      });

      cy.intercept(
        "DELETE",
        `/api/v1/plus/custom-metadata/custom-field/id-custom-field-starter-pokemon`,
        {
          statusCode: 204,
        }
      ).as("deleteStarter");
      cy.intercept("PUT", `/api/v1/plus/custom-metadata/custom-field`, {
        fixture: "taxonomy/custom-metadata/custom-field/update-party.json",
      }).as("updateParty");

      cy.getByTestId("submit-btn").click();

      cy.wait(["@updateParty", "@deleteStarter"]).then(
        ([updatePartyInterception]) => {
          expect(updatePartyInterception.request.body.id).to.eql(
            "id-custom-field-pokemon-party"
          );
          expect(updatePartyInterception.request.body.resource_id).to.eql(
            RESOURCE_CHILD.key
          );
          expect(updatePartyInterception.request.body.value).to.eql([
            "Charmander",
            "Eevee",
          ]);
        }
      );
    });
  });
});
