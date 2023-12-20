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
      });
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("Canada", false);
        assertIsChecked("United States", false);
      });
      cy.getByTestId("picker-card-South America").within(() => {
        assertIsChecked("Brazil", true);
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
        cy.getByTestId("num-selected-badge").contains("2 selected");

        // Unselect all
        cy.getByTestId("select-all").click();
        assertIsChecked("European Economic Area", false);
        cy.getByTestId("num-selected-badge").should("not.exist");

        // Toggle "regulated"
        cy.getByTestId("regulated-toggle").click();
        cy.getByTestId("European Economic Area-checkbox").should("not.exist");
      });

      // North America should have stayed the same through all this
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("Canada", false);
        assertIsChecked("United States", false);
        cy.getByTestId("num-selected-badge").contains("1 selected");
      });
    });

    it("can search", () => {
      // Search for 'Ca'
      cy.getByTestId("search-bar").type("Ca");
      cy.getByTestId("picker-card-Europe").should("not.exist");
      cy.getByTestId("picker-card-South America").should("not.exist");
      cy.getByTestId("picker-card-North America").within(() => {
        cy.getByTestId("California-checkbox");
      });

      // Clear search should reset to initial state
      cy.get("button").contains("Clear").click();
      cy.getByTestId("picker-card-Europe");
      cy.getByTestId("picker-card-North America");
      cy.getByTestId("picker-card-South America");

      // Search for 'co' (lowercase) should show across continents
      cy.getByTestId("search-bar").type("co");
      cy.getByTestId("picker-card-Europe").within(() => {
        cy.getByTestId("European Economic Area-checkbox");
      });
      cy.getByTestId("picker-card-North America").within(() => {
        cy.getByTestId("California-checkbox").should("not.exist");
        cy.getByTestId("Colorado-checkbox");
      });
    });

    it("renders and unrenders save button appropriately", () => {
      // Save button should not exist when there are no changes
      cy.getByTestId("save-btn").should("not.exist");

      // Uncheck Canada. Making a change should make save button appear
      cy.getByTestId("Canada-checkbox").click();
      assertIsChecked("Canada", true);
      cy.getByTestId("save-btn").should("exist");

      // Undoing the change should make save buttond disappear again
      cy.getByTestId("Canada-checkbox").click();
      assertIsChecked("Canada", false);
      cy.getByTestId("save-btn").should("not.exist");
    });

    it("can change selections and persist to the backend", () => {
      // Check Canada. Making a change should make save button appear
      cy.getByTestId("Canada-checkbox").click();
      assertIsChecked("Canada", true);

      // Check Brazil
      cy.getByTestId("Brazil-checkbox").click();
      assertIsChecked("Brazil", false);

      // Set up the next GET to return our changed data
      cy.fixture("locations/list.json").then((data) => {
        const newLocations = data.locations.map((l) => {
          if (l.name === "Canada") {
            return { ...l, selected: true };
          }
          if (l.name === "Quebec") {
            return { ...l, selected: true };
          }
          if (l.name === "Brazil") {
            return { ...l, selected: false };
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
            id: "ca",
            selected: true,
          },
          {
            id: "fr",
            selected: true,
          },
          {
            id: "it",
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
            id: "us_ct",
            selected: false,
          },
          {
            id: "us_va",
            selected: false,
          },
          {
            id: "us_ut",
            selected: false,
          },
          {
            id: "ca_qc",
            selected: true,
          },
          {
            id: "br",
            selected: false,
          },
        ]);
      });
      cy.wait("@getLocationsSecond");
      cy.getByTestId("save-btn").should("not.exist");
    });
  });

  describe("modal view", () => {
    it("can show the modal view with selections", () => {
      cy.getByTestId("picker-card-Europe").within(() => {
        cy.getByTestId("view-more-btn").click();
      });
      cy.getByTestId("subgroup-modal").should("be.visible");
      cy.getByTestId("subgroup-modal").within(() => {
        cy.getByTestId("num-selected-badge").should("contain", "1 selected");
        cy.getByTestId("European Economic Area-accordion").within(() => {
          assertIsChecked("France", true);
          assertIsChecked("Italy", false);
        });
      });
    });

    it("can select all", () => {
      cy.getByTestId("picker-card-Europe").within(() => {
        cy.getByTestId("view-more-btn").click();
      });
      cy.getByTestId("subgroup-modal").within(() => {
        cy.getByTestId("select-all").click();
        cy.getByTestId("num-selected-badge").should("contain", "2 selected");
        cy.getByTestId("European Economic Area-accordion").within(() => {
          assertIsChecked("France", true);
          assertIsChecked("Italy", true);
        });
      });
    });

    it("can apply selections back to continent view", () => {
      cy.getByTestId("picker-card-North America").within(() => {
        cy.getByTestId("view-more-btn").click();
      });
      // Selecting Quebec should also select Canada in the continent view since Quebec
      // is the only child of Canada
      cy.getByTestId("subgroup-modal").within(() => {
        cy.getByTestId("United States-accordion");
        cy.getByTestId("Canada-accordion").within(() => {
          cy.getByTestId("Quebec-checkbox").click();
        });
      });
      cy.getByTestId("apply-btn").click();
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("Canada", true);
        // Deselecting Canada here should also deselect Quebec in modal view
        cy.getByTestId("Canada-checkbox").click();
        cy.getByTestId("view-more-btn").click();
      });
      cy.getByTestId("subgroup-modal").within(() => {
        cy.getByTestId("Canada-accordion").within(() => {
          assertIsChecked("Quebec", false);
        });
      });
    });

    it("can view more for continents without subgroups", () => {
      cy.getByTestId("picker-card-South America").within(() => {
        cy.getByTestId("view-more-btn").click();
      });
      cy.getByTestId("subgroup-modal").within(() => {
        assertIsChecked("Brazil", true);
      });
    });
  });
});
