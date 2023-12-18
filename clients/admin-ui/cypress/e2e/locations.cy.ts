import { stubPlus } from "cypress/support/stubs";

import { LOCATIONS_ROUTE } from "~/features/common/nav/v2/routes";

const assertIsChecked = (name: string, checked: boolean) => {
  cy.getByTestId(`${name}-checkbox`).within(() => {
    const assertion = checked ? "be.checked" : "not.be.checked";
    cy.get("input").should(assertion);
  });
};

describe("Locations", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    cy.intercept("GET", "/api/v1/plus/locations", {
      fixture: "locations/list.json",
    }).as("getLocations");
    cy.intercept("PATCH", "/api/v1/plus/locations", {
      fixture: "locations/list.json",
    }).as("patchLocations");
    cy.visit(LOCATIONS_ROUTE);
    cy.getByTestId("location-management");
  });

  describe("continent view", () => {
    it("renders locations by continent from initial data", () => {
      cy.getByTestId("picker-card-Europe").within(() => {
        cy.getByTestId("select-all").should("not.be.checked");
        assertIsChecked("European Economic Area", false);
        assertIsChecked("France", true);
        assertIsChecked("Ile-de-France", false);
      });
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("United States", false);
        assertIsChecked("California", true);
        assertIsChecked("Colorado", true);
      });
    });

    it("can toggle and check appropriately", () => {
      cy.getByTestId("picker-card-Europe").within(() => {
        cy.getByTestId("select-all").within(() => {
          cy.get("input").should("not.be.checked");
        });
        // Select all
        cy.getByTestId("select-all").click();
        cy.getByTestId("select-all").within(() => {
          cy.get("input").should("be.checked");
        });
        assertIsChecked("European Economic Area", true);
        assertIsChecked("France", true);
        assertIsChecked("Ile-de-France", true);
        cy.getByTestId("num-selected-badge").contains("3 selected");

        // Unselect all
        cy.getByTestId("select-all").click();
        assertIsChecked("European Economic Area", false);
        assertIsChecked("France", false);
        assertIsChecked("Ile-de-France", false);
        cy.getByTestId("num-selected-badge").should("not.exist");

        // Toggle "regulated"
        cy.getByTestId("regulated-toggle").click();
        cy.getByTestId("European Economic Area-checkbox").should("not.exist");
        cy.getByTestId("France-checkbox");
        cy.getByTestId("Ile-de-France-checkbox");
      });

      // North America should have stayed the same through all this
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("United States", false);
        assertIsChecked("California", true);
        assertIsChecked("Colorado", true);
        cy.getByTestId("num-selected-badge").contains("2 selected");
      });
    });

    it("can search", () => {
      // Search for 'Fr'
      cy.getByTestId("search-bar").type("Fr");
      cy.getByTestId("picker-card-Europe").within(() => {
        cy.getByTestId("European Economic Area-checkbox").should("not.exist");
        cy.getByTestId("France-checkbox");
        cy.getByTestId("Ile-de-France-checkbox");
      });
      cy.getByTestId("picker-card-North America").should("not.exist");

      // Clear search should reset to initial state
      cy.get("button").contains("Clear").click();
      cy.getByTestId("picker-card-Europe");
      cy.getByTestId("picker-card-North America");

      // Search for 'co' (lowercase) should show across continents
      cy.getByTestId("search-bar").type("co");
      cy.getByTestId("picker-card-Europe").within(() => {
        cy.getByTestId("European Economic Area-checkbox");
        cy.getByTestId("France-checkbox").should("not.exist");
        cy.getByTestId("Ile-de-France-checkbox").should("not.exist");
      });
      cy.getByTestId("picker-card-North America").within(() => {
        cy.getByTestId("United States-checkbox").should("not.exist");
        cy.getByTestId("California-checkbox").should("not.exist");
        cy.getByTestId("Colorado-checkbox");
      });
    });

    it("renders and unrenders save button appropriately", () => {
      // Save button should not exist when there are no changes
      cy.getByTestId("save-btn").should("not.exist");

      // Uncheck Colorado. Making a change should make save button appear
      cy.getByTestId("Colorado-checkbox").click();
      assertIsChecked("Colorado", false);
      cy.getByTestId("save-btn").should("exist");

      // Undoing the change should make save buttond disappear again
      cy.getByTestId("Colorado-checkbox").click();
      assertIsChecked("Colorado", true);
      cy.getByTestId("save-btn").should("not.exist");
    });

    it("can change selections and persist to the backend", () => {
      // Uncheck Colorado. Making a change should make save button appear
      cy.getByTestId("Colorado-checkbox").click();
      assertIsChecked("Colorado", false);

      // Check Ile-de-France
      cy.getByTestId("Ile-de-France-checkbox").click();
      assertIsChecked("Ile-de-France", true);

      // Set up the next GET to return our changed data
      cy.fixture("locations/list.json").then((data) => {
        const newLocations = data.locations.map((l) => {
          if (l.name === "Colorado") {
            return { ...l, selected: false };
          }
          if (l.name === "Ile-de-France") {
            return { ...l, selected: true };
          }
          return l;
        });
        cy.intercept("GET", "/api/v1/plus/locations", {
          body: { ...data, locations: newLocations },
        }).as("getLocationsSecond");
      });

      cy.getByTestId("save-btn").click();
      cy.wait("@patchLocations").then((interception) => {
        const { body } = interception.request;
        // No changes to regulations
        expect(body.regulations).to.eql([]);
        // Check locations
        expect(body.locations).to.eql([
          {
            id: "us",
            selected: false,
          },
          {
            id: "eea",
            selected: false,
          },
          {
            id: "us_ca",
            selected: true,
          },
          {
            id: "us_co",
            selected: false,
          },
          {
            id: "fr",
            selected: true,
          },
          {
            id: "fr-idf",
            selected: true,
          },
        ]);
      });
      cy.wait("@getLocationsSecond");
      cy.getByTestId("save-btn").should("not.exist");
    });
  });
});
