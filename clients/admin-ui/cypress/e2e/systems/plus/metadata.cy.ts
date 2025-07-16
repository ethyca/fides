import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
  stubVendorList,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/routes";

describe("Plus Custom Metadata", () => {
  beforeEach(() => {
    cy.login();
    stubSystemCrud();
    stubTaxonomyEntities();
    stubPlus(true);
    cy.intercept("GET", "/api/v1/system", {
      fixture: "systems/systems.json",
    }).as("getSystems");
    cy.intercept({ method: "POST", url: "/api/v1/system*" }).as(
      "postDictSystem",
    );
    cy.intercept("/api/v1/config?api_set=false", {});
    stubDatasetCrud();
    stubSystemIntegrations();
    stubSystemVendors();
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
      `/api/v1/plus/custom-metadata/custom-field-definition/resource-type/*`,

      {
        fixture: "taxonomy/custom-metadata/custom-field-definition/list.json",
      },
    ).as("getCustomFieldDefinitions");
    cy.intercept(
      "GET",
      `/api/v1/plus/custom-metadata/custom-field/resource/*`,
      {
        fixture: "taxonomy/custom-metadata/custom-field/list.json",
      },
    ).as("getCustomFields");
    cy.intercept("POST", `/api/v1/plus/custom-metadata/custom-field/bulk`, {
      body: {},
    }).as("bulkUpdateCustomField");
    stubVendorList();
  });

  it("can populate initial custom metadata", () => {
    cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system`);
    cy.wait(["@getSystem", "@getDictionaryEntries"]);

    // Should not be able to save while form is untouched
    cy.getByTestId("save-btn").should("be.disabled");
    const testId =
      "controlled-select-customFieldValues.id-custom-field-definition-pokemon-party";
    cy.getByTestId(testId).contains("Charmander");
    cy.getByTestId(testId).contains("Eevee");
    cy.getByTestId(testId).contains("Snorlax");
    cy.getByTestId(testId).type("Bulbasaur{enter}");

    // Should be able to save now that form is dirty
    cy.getByTestId("save-btn").should("be.enabled");
    cy.getByTestId("save-btn").click();

    cy.wait("@putSystem");

    const expectedValues = [
      {
        custom_field_definition_id: "id-custom-field-definition-pokemon-party",
        id: "id-custom-field-pokemon-party",
        resource_id: "demo_analytics_system",
        value: ["Charmander", "Eevee", "Snorlax", "Bulbasaur"],
      },
      {
        custom_field_definition_id:
          "id-custom-field-definition-starter-pokemon",
        id: "id-custom-field-starter-pokemon",
        resource_id: "demo_analytics_system",
        value: "Squirtle",
      },
    ];
    cy.wait("@bulkUpdateCustomField").then((interception) => {
      expect(interception.request.body.upsert).to.eql(expectedValues);
    });
  });
});
