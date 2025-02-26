import { stubLocations, stubPlus } from "cypress/support/stubs";

import {
  LOCATIONS_ROUTE,
  REGULATIONS_ROUTE,
} from "~/features/common/nav/routes";

const assertIsChecked = (
  name: string,
  state: "checked" | "unchecked" | "indeterminate",
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

describe("Locations and regulations", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubLocations();
  });

  describe("location continent view", () => {
    beforeEach(() => {
      cy.visit(LOCATIONS_ROUTE);
      cy.getByTestId("location-management");
    });
    it("renders locations by continent from initial data", () => {
      cy.getByTestId("picker-card-Europe").within(() => {
        assertIsChecked("select-all", "indeterminate");
        assertIsChecked(
          "European Economic Area (EEA)-checkbox",
          "indeterminate",
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

      // Toggle "regulated" in Africa which has no regulations
      cy.getByTestId("picker-card-Africa").within(() => {
        cy.getByTestId("Eritrea-checkbox");
        cy.getByTestId("regulated-toggle").click();
        cy.getByTestId("Eritrea-checkbox").should("not.exist");
        cy.getByTestId("regulated-toggle").click();
        cy.getByTestId("Eritrea-checkbox");
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

      // Searching 'can' and then selecting 'Canada' should also select Quebec
      // (despite Quebec not containing 'can')
      cy.getByTestId("search-bar").clear().type("can");
      cy.getByTestId("picker-card-North America").within(() => {
        cy.getByTestId("Quebec-checkbox").should("not.exist");
        cy.getByTestId("Canada-checkbox").click();
        assertIsChecked("Canada-checkbox", "checked");
        cy.getByTestId("view-more-btn").click();
      });
      cy.getByTestId("Canada-accordion")
        .click()
        .within(() => {
          assertIsChecked("Quebec-checkbox", "checked");
        });
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
            id: "er",
            selected: false,
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

  describe("location modal view", () => {
    beforeEach(() => {
      cy.visit(LOCATIONS_ROUTE);
      cy.getByTestId("location-management");
    });
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
        assertIsChecked("select-all", "indeterminate");
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

  describe("regulations page", () => {
    beforeEach(() => {
      cy.visit(REGULATIONS_ROUTE);
      cy.getByTestId("regulation-management");
    });

    it("can view picker cards with regulations", () => {
      cy.getByTestId("picker-card-Europe").within(() => {
        assertIsChecked("GDPR (European Union)-checkbox", "checked");
      });
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("CCPA (California)-checkbox", "checked");
        assertIsChecked("CPA (Colorado)-checkbox", "unchecked");
        assertIsChecked("CTDPA (Connecticut)-checkbox", "unchecked");
        assertIsChecked("Law 25 (Quebec)-checkbox", "unchecked");
        assertIsChecked("PIPEDA (Canada)-checkbox", "unchecked");
      });
      cy.getByTestId("picker-card-South America").within(() => {
        assertIsChecked("LGPD (Brazil)-checkbox", "checked");
      });
    });

    it("can save updated regulations", () => {
      // Uncheck GDPR
      cy.getByTestId("GDPR (European Union)-checkbox").click();
      assertIsChecked("GDPR (European Union)-checkbox", "unchecked");

      // Check CPA
      cy.getByTestId("CPA (Colorado)-checkbox").click();
      assertIsChecked("CPA (Colorado)-checkbox", "checked");

      // Set up the next GET to return our changed data
      cy.fixture("locations/list.json").then((data) => {
        const newRegulations = data.regulations.map((r) => {
          if (r.id === "gdpr") {
            return { ...r, selected: false };
          }
          if (r.id === "cpa") {
            return { ...r, selected: true };
          }
          return r;
        });
        cy.intercept("GET", "/api/v1/plus/locations", {
          body: { ...data, regulations: newRegulations },
        }).as("getRegulationsSecond");
      });

      cy.getByTestId("save-btn").click();
      cy.getByTestId("continue-btn").click();
      cy.wait("@patchLocations").then((interception) => {
        const { body } = interception.request;
        // No changes to locations
        expect(body.locations).to.eql([]);
        // Check regulations
        expect(body.regulations).to.eql([
          {
            id: "gdpr",
            selected: false,
          },
          {
            id: "ccpa",
            selected: true,
          },
          {
            id: "cpa",
            selected: true,
          },
          {
            id: "vcdpa",
            selected: false,
          },
          {
            id: "ctdpa",
            selected: false,
          },
          {
            id: "ucpa",
            selected: false,
          },
          {
            id: "pipeda",
            selected: false,
          },
          {
            id: "law_25_quebec",
            selected: false,
          },
          {
            id: "lgpd",
            selected: true,
          },
        ]);
      });
      cy.wait("@getRegulationsSecond");
      cy.getByTestId("save-btn").should("not.exist");
    });

    it("can open the modal", () => {
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("select-all", "indeterminate");
        cy.getByTestId("view-more-btn").click();
      });
      cy.getByTestId("regulation-modal").within(() => {
        assertIsChecked("select-all", "indeterminate");
        assertIsChecked("CCPA (California)-checkbox", "checked");
        // Check a few more
        cy.getByTestId("Law 25 (Quebec)-checkbox").click();
        assertIsChecked("Law 25 (Quebec)-checkbox", "checked");
        cy.getByTestId("UCPA (Utah)-checkbox").click();
        assertIsChecked("UCPA (Utah)-checkbox", "checked");
        cy.getByTestId("apply-btn").click();
      });
      // Make sure checkboxes applied
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("Law 25 (Quebec)-checkbox", "checked");
        cy.getByTestId("view-more-btn").click();
      });
      // Try opening modal, making choices, then canceling
      cy.getByTestId("regulation-modal").within(() => {
        // Uncheck Law 25
        cy.getByTestId("Law 25 (Quebec)-checkbox").click();
        assertIsChecked("Law 25 (Quebec)-checkbox", "unchecked");
        cy.getByTestId("cancel-btn").click();
      });
      // Law 25 should still be applied
      cy.getByTestId("picker-card-North America").within(() => {
        assertIsChecked("Law 25 (Quebec)-checkbox", "checked");
        cy.getByTestId("view-more-btn").click();
      });
    });

    it("unsaved changes in cards propagate to modal", () => {
      cy.getByTestId("picker-card-North America").within(() => {
        cy.getByTestId("Law 25 (Quebec)-checkbox").click();
        cy.getByTestId("view-more-btn").click();
      });
      cy.getByTestId("regulation-modal").within(() => {
        assertIsChecked("Law 25 (Quebec)-checkbox", "checked");
      });
    });
  });
});
