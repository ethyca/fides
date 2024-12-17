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
  const RESOURCE_CHILD = {
    label: "Job Title",
    key: "user.job_title",
  };

  const navigateToEditor = () => {
    cy.getByTestId(`taxonomy-node-${RESOURCE_CHILD.key}`).click({});
  };

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
      "select-custom-fields-form_id-custom-field-definition-starter-pokemon";
    const testIdMulti =
      "select-custom-fields-form_id-custom-field-definition-pokemon-party";

    it("initializes form fields with values returned by the API", () => {
      cy.getByTestId("custom-fields-form");
      cy.getByTestId(testIdSingle).contains("Squirtle");

      ["Charmander", "Eevee", "Snorlax"].forEach((value) => {
        cy.getByTestId(testIdMulti).contains(value);
      });
    });

    it("allows choosing and changing selections", () => {
      cy.getByTestId("custom-fields-form");

      cy.getByTestId(testIdSingle).antClearSelect();
      cy.getByTestId(testIdSingle).antSelect("Snorlax");
      cy.getByTestId(testIdSingle).contains("Snorlax");
      cy.getByTestId(testIdSingle).antClearSelect();

      cy.getByTestId(testIdMulti).antRemoveSelectTag("Eevee");
      cy.getByTestId(testIdMulti).antRemoveSelectTag("Snorlax");

      cy.getByTestId(testIdMulti).antSelect("Eevee");

      ["Charmander", "Eevee"].forEach((value) => {
        cy.getByTestId(testIdMulti).contains(value);
      });

      cy.intercept("POST", `/api/v1/plus/custom-metadata/custom-field/bulk`, {
        body: {},
      }).as("bulkUpdateCustomField");

      cy.getByTestId("save-btn").click();

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
