import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
  stubVendorList,
} from "cypress/support/stubs";

import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_MULTIPLE_ROUTE,
  ADD_SYSTEMS_ROUTE,
  DATAMAP_ROUTE,
  INDEX_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";
import { RoleRegistryEnum } from "~/types/api";

describe("System management with Plus features", () => {
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
    stubDatasetCrud();
    stubSystemIntegrations();
    stubSystemVendors();
  });

  describe("permissions", () => {
    it("can view a system page as a viewer", () => {
      cy.assumeRole(RoleRegistryEnum.VIEWER);
      cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system`);
      cy.getByTestId("input-name").should("exist");
    });
  });

  describe("vendor list", () => {
    beforeEach(() => {
      stubVendorList();
      cy.visit(`${ADD_SYSTEMS_MANUAL_ROUTE}`);
      cy.wait(["@getDictionaryEntries", "@getSystems"]);
    });

    it("can display the vendor list dropdown", () => {
      cy.getByTestId("vendor-name-select");
    });

    it("contains type ahead dictionary entries", () => {
      cy.getByTestId("vendor-name-select").find("input").type("A");
      cy.get(".ant-select-item").eq(0).contains("Aniview LTD");
      cy.get(".ant-select-item").eq(1).contains("Anzu Virtual Reality LTD");
    });

    it("can reset suggestions by clearing vendor input", () => {
      cy.getByTestId("vendor-name-select").find("input").type("L");
      cy.antSelectDropdownVisible();
      cy.getByTestId("vendor-name-select").realPress("Enter");
      cy.getByTestId("input-legal_name").should("have.value", "LINE");
      cy.getByTestId("clear-btn").click();
      cy.getByTestId("input-legal_name").should("be.empty");
    });

    it("can't refresh suggestions immediately after populating", () => {
      cy.getByTestId("vendor-name-select").find("input").type("A{enter}");
      cy.getByTestId("refresh-suggestions-btn").should("be.disabled");
    });

    it("can refresh suggestions when editing a saved system", () => {
      cy.getByTestId("vendor-name-select").find("input").type("A{enter}");
      cy.fixture("systems/dictionary-system.json").then((dictSystem) => {
        cy.fixture("systems/system.json").then((origSystem) => {
          cy.intercept(
            { method: "GET", url: "/api/v1/system/demo_analytics_system" },
            {
              body: {
                ...origSystem,
                ...dictSystem,
                fides_key: origSystem.fides_key,
                customFieldValues: undefined,
              },
            },
          ).as("getDictSystem");
        });
      });
      cy.getByTestId("save-btn").click();
      cy.wait("@postDictSystem");
      cy.wait("@getDictSystem");
      cy.getByTestId("refresh-suggestions-btn").should("not.be.disabled");
    });

    // some DictSuggestionTextInputs don't get populated right, causing
    // the form to be mistakenly marked as dirty and the "unsaved changes"
    // modal to pop up incorrectly when switching tabs
    it("can switch between tabs after populating from dictionary", () => {
      cy.getByTestId("vendor-name-select").find("input").type("Anzu{enter}");
      // the form fetches the system again after saving, so update the intercept with dictionary values
      cy.fixture("systems/dictionary-system.json").then((dictSystem) => {
        cy.fixture("systems/system.json").then((origSystem) => {
          cy.intercept(
            { method: "GET", url: "/api/v1/system/demo_analytics_system" },
            {
              body: {
                ...origSystem,
                ...dictSystem,
                fides_key: origSystem.fides_key,
                customFieldValues: undefined,
              },
            },
          ).as("getDictSystem");
        });
      });
      cy.getByTestId("save-btn").click();
      cy.wait("@postDictSystem");
      cy.wait("@getDictSystem");
      cy.getByTestId("input-dpo").should("have.value", "DPO@anzu.io");
      cy.getByTestId("tab-Data uses").click();
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500);
      cy.getByTestId("tab-Information").click();
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500);
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("confirmation-modal").should("not.exist");
    });

    it("locks editing for a GVL vendor when TCF is enabled", () => {
      cy.getByTestId("vendor-name-select").find("input").type("Aniview{enter}");
      cy.getByTestId("locked-for-GVL-notice");
      cy.getByTestId("input-description").should("be.disabled");
    });

    it("does not allow changes to data uses when locked", () => {
      cy.getByTestId("vendor-name-select").find("input").type("Aniview{enter}");
      cy.getByTestId("save-btn").click();
      cy.wait(["@postSystem", "@getSystem", "@getSystems"]);
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("add-btn").should("not.exist");
      cy.getByTestId("delete-btn").should("not.exist");
      cy.getByTestId("row-functional.service.improve").click();
      cy.getByTestId("input-name").should("be.disabled");
    });

    it("does not lock editing for a non-GVL vendor", () => {
      cy.getByTestId("vendor-name-select").find("input").type("L{enter}");
      cy.getByTestId("locked-for-GVL-notice").should("not.exist");
      cy.getByTestId("input-description").should("not.be.disabled");
    });

    it("locks editing fields and changing name for a GVL vendor when visiting 'edit system' page directly", () => {
      cy.fixture("systems/system.json").then((system) => {
        cy.intercept("GET", "/api/v1/system/*", {
          body: {
            ...system,
            vendor_id: "gvl.733",
          },
        }).as("getSystemGVL");
      });
      cy.visit("/systems/configure/fidesctl_system");
      cy.wait("@getSystemGVL");
      cy.getByTestId("locked-for-GVL-notice");
      cy.getByTestId("input-name").should("be.disabled");
      cy.getByTestId("input-description").should("be.disabled");
    });

    it("does not lock editing for a non-GVL vendor when visiting 'edit system' page directly", () => {
      cy.fixture("systems/systems.json").then((systems) => {
        cy.intercept("GET", "/api/v1/system/*", {
          body: {
            ...systems[0],
            vendor_id: "gacp.3073",
          },
        }).as("getSystemNonGVL");
      });
      cy.visit("/systems/configure/fidesctl_system");
      cy.wait("@getSystemNonGVL");
      cy.getByTestId("locked-for-GVL-notice").should("not.exist");
      cy.getByTestId("input-name").should("not.be.disabled");
    });

    it("allows changes to data uses for non-GVL vendors", () => {
      cy.getByTestId("vendor-name-select").find("input").type("L");
      cy.antSelectDropdownVisible();
      cy.getByTestId("vendor-name-select").realPress("Enter");
      cy.getByTestId("save-btn").click();
      cy.wait(["@postSystem", "@getSystem", "@getSystems"]);
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("add-btn");
      cy.getByTestId("delete-btn");
      cy.getByTestId("row-functional.service.improve").click();
      cy.getByTestId("controlled-select-data_categories")
        .find("input")
        .should("not.be.disabled");
    });

    it("don't allow editing declaration name after creation", () => {
      cy.getByTestId("vendor-name-select").find("input").type("L{enter}");
      cy.getByTestId("save-btn").click();
      cy.wait(["@postSystem", "@getSystem", "@getSystems"]);
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("row-functional.service.improve").click();
      cy.getByTestId("input-name").should("be.disabled");
    });

    it("don't allow editing data uses after creation", () => {
      cy.getByTestId("vendor-name-select").find("input").type("L");
      cy.antSelectDropdownVisible();
      cy.getByTestId("vendor-name-select").realPress("Enter");
      cy.getByTestId("save-btn").click();
      cy.wait(["@postSystem", "@getSystem", "@getSystems"]);
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("row-functional.service.improve").click();
      cy.getByTestId("controlled-select-data_use")
        .find("input")
        .should("be.disabled");
    });
  });

  describe("custom metadata", () => {
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
          custom_field_definition_id:
            "id-custom-field-definition-pokemon-party",
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

  describe("bulk system/vendor adding page", () => {
    beforeEach(() => {
      stubPlus(true);
      stubSystemVendors();
    });

    it("page loads with table and rows", () => {
      cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);

      cy.wait("@getSystemVendors");
      cy.getByTestId("fidesTable");
      cy.getByTestId("fidesTable-body")
        .find("tr")
        .should("have.length.greaterThan", 0);
    });

    it("upgrade modal doesn't pop up if compass is enabled", () => {
      cy.visit(ADD_SYSTEMS_ROUTE);
      cy.getByTestId("multiple-btn").click();
      cy.wait("@getSystemVendors");
      cy.getByTestId("fidesTable");
    });

    it("upgrade modal pops up if compass isn't enabled and redirects to manual add", () => {
      stubPlus(true, {
        core_fides_version: "2.2.0",
        fidesplus_server: "healthy",
        system_scanner: {
          enabled: true,
          cluster_health: null,
          cluster_error: null,
        },
        dictionary: {
          enabled: false,
          service_health: null,
          service_error: null,
        },
        tcf: {
          enabled: true,
        },
        fidesplus_version: "",
        fides_cloud: {
          enabled: false,
        },
      });
      cy.visit(ADD_SYSTEMS_ROUTE);
      cy.getByTestId("multiple-btn").click();
      cy.getByTestId("confirmation-modal");
      cy.getByTestId("cancel-btn").click();
      cy.url().should("include", ADD_SYSTEMS_MANUAL_ROUTE);
    });

    it("can add new systems and redirects to datamap", () => {
      cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
      cy.wait("@getSystemVendors");
      cy.get('[type="checkbox"').check({ force: true });
      cy.getByTestId("add-multiple-systems-btn")
        .should("exist")
        .click({ force: true });
      cy.getByTestId("confirmation-modal");
      cy.getByTestId("continue-btn").click({ force: true });
      cy.url().should("include", DATAMAP_ROUTE);
    });

    it("select page checkbox only selects rows on the displayed page", () => {
      cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
      cy.wait("@getSystemVendors");
      cy.getByTestId("select-page-checkbox")
        .get("[type='checkbox']")
        .check({ force: true });
      cy.getByTestId("selected-row-count").contains("6 row(s) selected.");
    });

    it("select all button selects all rows across every page", () => {
      cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
      cy.wait("@getSystemVendors");
      cy.getByTestId("select-page-checkbox")
        .get("[type='checkbox']")
        .check({ force: true });
      cy.getByTestId("select-all-rows-btn").click();
      cy.getByTestId("selected-row-count").contains("8 row(s) selected.");
    });

    it("filter button and sources column are hidden when TCF is disabled", () => {
      stubPlus(true, {
        core_fides_version: "2.2.0",
        fidesplus_server: "healthy",
        system_scanner: {
          enabled: true,
          cluster_health: null,
          cluster_error: null,
        },
        dictionary: {
          enabled: true,
          service_health: null,
          service_error: null,
        },
        tcf: {
          enabled: false,
        },
        fidesplus_version: "",
        fides_cloud: {
          enabled: false,
        },
      });
      cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
      cy.getByTestId("filter-multiple-systems-btn").should("not.exist");
      cy.getByTestId("column-vendor_id").should("not.exist");
    });

    it("filter button and sources column are shown when TCF is enabled", () => {
      cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
      cy.getByTestId("filter-multiple-systems-btn").should("exist");
      cy.getByTestId("column-vendor_id").should("exist");
    });

    it("filter modal state is persisted after modal is closed", () => {
      cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
      cy.getByTestId("filter-multiple-systems-btn").click();
      cy.get("#checkbox-gvl").check({ force: true });
      cy.getByTestId("filter-done-btn").click();
      cy.getByTestId("filter-multiple-systems-btn").click();
      cy.get("#checkbox-gvl").should("be.checked");
    });

    it("pagination menu updates pagesize", () => {
      cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);

      cy.wait("@getSystemVendors");
      cy.getByTestId("fidesTable");
      cy.getByTestId("fidesTable-body").find("tr").should("have.length", 25);
      cy.getByTestId("pagination-btn").click();
      cy.getByTestId("pageSize-50").click();
      cy.getByTestId("fidesTable-body").find("tr").should("have.length", 50);
    });

    it("redirects to index when compass is disabled", () => {
      stubPlus(true, {
        core_fides_version: "2.2.0",
        fidesplus_server: "healthy",
        system_scanner: {
          enabled: true,
          cluster_health: null,
          cluster_error: null,
        },
        dictionary: {
          enabled: false,
          service_health: null,
          service_error: null,
        },
        tcf: {
          enabled: false,
        },
        fidesplus_version: "",
        fides_cloud: {
          enabled: false,
        },
      });
      cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
      cy.location().should((location) => {
        expect(location.pathname).to.eq(INDEX_ROUTE);
      });
    });
  });

  describe("tab navigation", () => {
    it("updates URL hash when switching tabs", () => {
      cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system#information`);
      cy.location("hash").should("eq", "#information");

      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500);
      cy.getByTestId("tab-Data uses").click();
      cy.location("hash").should("eq", "#data-uses");

      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500);
      cy.getByTestId("tab-Data flow").click();
      cy.location("hash").should("eq", "#data-flow");

      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500);
      cy.getByTestId("tab-Integrations").click();
      cy.location("hash").should("eq", "#integrations");

      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500);
      cy.getByTestId("tab-History").click();
      cy.location("hash").should("eq", "#history");
    });

    it("loads correct tab directly based on URL hash", () => {
      // Visit page with specific hash
      cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system#data-uses`);

      // Verify correct tab is active
      cy.getByTestId("tab-Data uses").should(
        "have.attr",
        "aria-selected",
        "true",
      );
      cy.location("hash").should("eq", "#data-uses");
    });
  });
});
