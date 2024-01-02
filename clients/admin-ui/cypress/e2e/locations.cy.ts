import { stubPlus } from "cypress/support/stubs";

import { LOCATIONS_ROUTE } from "~/features/common/nav/v2/routes";

const assertIsChecked = (
  name: string,
  state: "checked" | "unchecked" | "indeterminate"
) => {
  cy.getByTestId(name).within(() => {
    if (state === "indeterminate") {
      cy.get("input").should("have.prop", "indeterminate");
    } else {
      const assertion = state === "checked" ? "be.checked" : "not.be.checked";
      cy.get("input").should(assertion);
    }
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
        assertIsChecked("select-all", "indeterminate");
        assertIsChecked(
          "European Economic Area (EEA)-checkbox",
          "indeterminate"
        );
      });
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("Canada-checkbox", "unchecked");
        assertIsChecked("United States-checkbox", "indeterminate");
      });
      cy.getByTestId("picker-card-South America").within(() => {
        assertIsChecked("Brazil-checkbox", "checked");
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
        assertIsChecked("European Economic Area (EEA)-checkbox", "checked");
        cy.getByTestId("num-selected-badge").contains("2 selected");

        // Unselect all
        cy.getByTestId("select-all").click();
        assertIsChecked("European Economic Area (EEA)-checkbox", "unchecked");
        cy.getByTestId("num-selected-badge").should("not.exist");

        // Toggle "regulated". EEA itself is not regulated, but its composing regions are
        // so it should still be around
        cy.getByTestId("regulated-toggle").click();
        cy.getByTestId("European Economic Area (EEA)-checkbox");
      });

      // Toggle "regulated" in South America which has some regulations
      cy.getByTestId("picker-card-South America").within(() => {
        cy.getByTestId("Brazil-checkbox");
        cy.getByTestId("Venezuela-checkbox");
        cy.getByTestId("regulated-toggle").click();
        cy.getByTestId("Brazil-checkbox");
        cy.getByTestId("Venezuela-checkbox").should("not.exist");
      });

      // North America should have stayed the same through all this
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("Canada-checkbox", "unchecked");
        assertIsChecked("United States-checkbox", "indeterminate");
        cy.getByTestId("num-selected-badge").contains("1 selected");
      });
    });

    it("can search", () => {
      // Search for 'Cal'
      cy.getByTestId("search-bar").type("Cal");
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

      // Search for 'co' (lowercase)
      cy.getByTestId("search-bar").type("co");
      cy.getByTestId("picker-card-North America").within(() => {
        cy.getByTestId("California-checkbox").should("not.exist");
        cy.getByTestId("Colorado-checkbox");
        cy.getByTestId("Connecticut-checkbox");
        // Checking colorado should make North America indeterminate
        cy.getByTestId("Colorado-checkbox").click();
        assertIsChecked("Colorado-checkbox", "checked");
        assertIsChecked("select-all", "indeterminate");
        // Now check all
        cy.getByTestId("select-all").click();
      });
      // Removing the 'o' from the search should only show checked 'co's
      cy.getByTestId("search-bar").type("{backspace}");
      assertIsChecked("Colorado-checkbox", "checked");
      assertIsChecked("Connecticut-checkbox", "checked");
      assertIsChecked("Quebec-checkbox", "unchecked");
      assertIsChecked("Canada-checkbox", "unchecked");

      // Checking Canada should also check Quebec
      cy.getByTestId("Canada-checkbox").click();
      assertIsChecked("Quebec-checkbox", "checked");

      // Unchecking Quebec should also uncheck Canada
      cy.getByTestId("Quebec-checkbox").click();
      assertIsChecked("Canada-checkbox", "unchecked");
    });

    it("renders and unrenders save button appropriately", () => {
      // Save button should not exist when there are no changes
      cy.getByTestId("save-btn").should("not.exist");

      // Check Canada. Making a change should make save button appear
      cy.getByTestId("Canada-checkbox").click();
      assertIsChecked("Canada-checkbox", "checked");
      cy.getByTestId("save-btn").should("exist");

      // Undoing the change should make save buttond disappear again
      cy.getByTestId("Canada-checkbox").click();
      assertIsChecked("Canada-checkbox", "unchecked");
      cy.getByTestId("save-btn").should("not.exist");
    });

    it("can change selections and persist to the backend", () => {
      // Check Canada
      cy.getByTestId("Canada-checkbox").click();
      assertIsChecked("Canada-checkbox", "checked");

      // Uncheck Brazil
      cy.getByTestId("Brazil-checkbox").click();
      assertIsChecked("Brazil-checkbox", "unchecked");

      // Set up the next GET to return our changed data
      cy.fixture("locations/list.json").then((data) => {
        const newLocations = data.locations.map((l) => {
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
      cy.getByTestId("continue-btn").click();
      cy.wait("@patchLocations").then((interception) => {
        const { body } = interception.request;
        // No changes to regulations
        expect(body.regulations).to.eql([]);
        // Check locations
        expect(body.locations).to.eql([
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
          {
            id: "ve",
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
        cy.getByTestId("European Economic Area (EEA)-accordion")
          .click()
          .within(() => {
            assertIsChecked("France-checkbox", "checked");
            assertIsChecked("Italy-checkbox", "unchecked");
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
        cy.getByTestId("European Economic Area (EEA)-accordion")
          .click()
          .within(() => {
            assertIsChecked("France-checkbox", "checked");
            assertIsChecked("Italy-checkbox", "checked");
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
        cy.getByTestId("United States-accordion").click();
        cy.getByTestId("Canada-accordion")
          .click()
          .within(() => {
            cy.getByTestId("Quebec-checkbox").click();
          });
      });
      cy.getByTestId("apply-btn").click();
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("Canada-checkbox", "checked");
        // Deselecting Canada here should also deselect Quebec in modal view
        cy.getByTestId("Canada-checkbox").click();
        cy.getByTestId("view-more-btn").click();
      });
      cy.getByTestId("subgroup-modal").within(() => {
        cy.getByTestId("Canada-accordion")
          .click()
          .within(() => {
            assertIsChecked("Quebec-checkbox", "unchecked");
          });
      });
    });

    it("can apply indeterminate selections back to continent view", () => {
      cy.getByTestId("picker-card-North America").within(() => {
        // Turn all of U.S. on
        cy.getByTestId("United States-checkbox").click();
        cy.getByTestId("num-selected-badge").should("contain", "5 selected");
        cy.getByTestId("view-more-btn").click();
      });
      // Deselect California
      cy.getByTestId("subgroup-modal").within(() => {
        cy.getByTestId("United States-accordion")
          .click()
          .within(() => {
            cy.getByTestId("California-checkbox").click();
          });
      });
      cy.getByTestId("apply-btn").click();
      // US should now be indeterminate
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("United States-checkbox", "indeterminate");
        cy.getByTestId("num-selected-badge").should("contain", "4 selected");
      });
    });

    it("can view more for continents without subgroups", () => {
      cy.getByTestId("picker-card-South America").within(() => {
        cy.getByTestId("view-more-btn").click();
      });
      cy.getByTestId("subgroup-modal").within(() => {
        // Don't render "Other" if there are only Other's
        cy.getByTestId("Other-accordion").should("not.exist");
        assertIsChecked("Brazil-checkbox", "checked");
        assertIsChecked("Venezuela-checkbox", "unchecked");
      });
    });
  });
});
