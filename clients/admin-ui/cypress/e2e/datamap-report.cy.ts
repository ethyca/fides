import {
  stubPlus,
  stubSystemCrud,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { REPORTING_DATAMAP_ROUTE } from "~/features/common/nav/v2/routes";
import {
  AllowedTypes,
  CustomFieldDefinition,
  ResourceTypes,
} from "~/types/api";

const mockCustomField = (overrides?: Partial<CustomFieldDefinition>) => {
  const base = {
    name: "Prime number",
    description: null,
    field_type: "string",
    allow_list_id: "id-allow-list-prime-numbers",
    resource_type: "system",
    field_definition: null,
    active: true,
    id: "id-custom-field-definition-prime-number",
  };
  if (overrides) {
    return { ...base, ...overrides };
  }
  return base;
};

describe("Minimal datamap report table", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubSystemCrud();
    stubTaxonomyEntities();
    cy.intercept("GET", "/api/v1/plus/datamap/minimal*", {
      fixture: "datamap/minimal.json",
    }).as("getDatamapMinimal");
    cy.intercept(
      "GET",
      "/api/v1/plus/custom-metadata/custom-field-definition",
      {
        body: [
          mockCustomField({ name: "Starter pokemon" }),
          mockCustomField({
            name: "Pokemon party",
            // eslint-disable-next-line no-underscore-dangle
            field_type: AllowedTypes.STRING_,
          }),
          mockCustomField({
            name: "color",
            resource_type: ResourceTypes.DATA_USE,
          }),
        ],
      }
    );
    cy.visit(REPORTING_DATAMAP_ROUTE);
  });

  it("can render custom fields", () => {
    // Should render the custom fields as columns
    cy.getByTestId("column-system_starter_pokemon").contains("Starter pokemon");
    cy.getByTestId("column-system_pokemon_party").contains("Pokemon party");
    cy.getByTestId("column-privacy_declaration_color").contains("Color");

    // Pokemon party is multi-select, so we should have a menu to allow grouping/displaying all
    cy.getByTestId("row-0-col-system_pokemon_party").contains("3");
    cy.getByTestId("system_pokemon_party-header-menu").click();
    cy.getByTestId("system_pokemon_party-header-menu-list").within(() => {
      cy.get("button").contains("Display all").click();
    });
    ["eevee", "pikachu", "articuno"].forEach((pokemon) => {
      cy.getByTestId("row-0-col-system_pokemon_party").contains(pokemon);
    });
  });

  it("can render empty datamap report", () => {
    cy.intercept("GET", "/api/v1/plus/datamap/minimal*", {
      body: { items: [], page: 1, pages: 0, size: 25, total: 0 },
    }).as("getDatamapMinimalEmpty");
    cy.getByTestId("datamap-report-heading").should("be.visible");
  });

  describe("Undeclared data category columns", () => {
    it("should have the undeclared data columns disabled by default", () => {
      cy.getByTestId("row-0-col-system_undeclared_data_categories").should(
        "not.exist"
      );
      cy.getByTestId("row-0-col-data_use_undeclared_data_categories").should(
        "not.exist"
      );
    });

    it("should show undeclared data columns when enabled", () => {
      cy.getByTestId("edit-columns-btn").click();
      cy.contains("div", "System undeclared data categories").click();
      cy.contains("div", "Data use undeclared data categories").click();
      cy.getByTestId("save-button").click();

      cy.getByTestId("row-0-col-system_undeclared_data_categories").contains(
        "2 system undeclared data categories"
      );
      cy.getByTestId("row-0-col-data_use_undeclared_data_categories").contains(
        "2 data use undeclared data categories"
      );

      // should be able to expand columns
      cy.getByTestId("system_undeclared_data_categories-header-menu").click();
      cy.getByTestId(
        "system_undeclared_data_categories-header-menu-list"
      ).within(() => {
        cy.get("button").contains("Display all").click();
      });
      ["User Contact Email", "Cookie ID"].forEach((pokemon) => {
        cy.getByTestId("row-0-col-system_undeclared_data_categories").contains(
          pokemon
        );
      });

      cy.getByTestId("data_use_undeclared_data_categories-header-menu").click();
      cy.getByTestId(
        "data_use_undeclared_data_categories-header-menu-list"
      ).within(() => {
        cy.get("button").contains("Display all").click();
      });
      ["User Contact Email", "Cookie ID"].forEach((pokemon) => {
        cy.getByTestId(
          "row-0-col-data_use_undeclared_data_categories"
        ).contains(pokemon);
      });
    });
  });

  describe("Exporting", () => {
    it("should open the export modal", () => {
      cy.getByTestId("export-btn").click();
      cy.getByTestId("export-modal").should("be.visible");
      cy.getByTestId("export-format-select").should("be.visible");
      cy.getByTestId("export-modal-continue-btn").should(
        "contain.text",
        "Download"
      );
      cy.getByTestId("export-modal-cancel-btn").click();
      cy.getByTestId("export-modal").should("not.exist");
    });

    // ideally we should test the downloads, but it's a bit complex and time consuming so deferring for now
    it.skip("should download the export file", () => {});
  });
});
