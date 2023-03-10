import { stubPlus } from "cypress/support/stubs";

import { RoleRegistryEnum } from "~/types/api";

const ALL_TILES = [
  "View data map",
  "Add systems",
  "View systems",
  "Configure privacy requests",
  "Review privacy requests",
];

const verifyExpectedTiles = (expectedTiles: string[]) => {
  expectedTiles.forEach((tile) => {
    cy.getByTestId(`tile-${tile}`);
  });
  const remainingTiles = ALL_TILES.filter((t) => !expectedTiles.includes(t));
  remainingTiles.forEach((item) => {
    cy.getByTestId(`tile-${item}`).should("not.exist");
  });
};

describe("Home page", () => {
  beforeEach(() => {
    cy.login();
  });

  // TODO: temporarily disabled due to https://github.com/ethyca/fides/issues/2769
  describe.skip("permissions", () => {
    beforeEach(() => {
      // For these tests, let's say we always have systems and connectors
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
      cy.intercept("GET", "/api/v1/connection*", {
        fixture: "connectors/list.json",
      }).as("getConnectors");
      stubPlus(true);
    });

    it("renders all tiles when all scopes are available", () => {
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.visit("/");
      verifyExpectedTiles(ALL_TILES);
    });

    it("renders all tiles as contributor", () => {
      cy.assumeRole(RoleRegistryEnum.CONTRIBUTOR);
      cy.visit("/");
      verifyExpectedTiles(ALL_TILES);
    });

    it("renders viewer only tiles", () => {
      cy.assumeRole(RoleRegistryEnum.VIEWER);
      cy.visit("/");
      verifyExpectedTiles(["View data map", "View systems"]);
    });

    it("renders privacy request manager tiles", () => {
      cy.assumeRole(RoleRegistryEnum.APPROVER);
      cy.visit("/");
      verifyExpectedTiles(["Review privacy requests"]);
    });

    it("renders privacy request manager + viewer tiles", () => {
      cy.assumeRole(RoleRegistryEnum.VIEWER_AND_APPROVER);
      cy.visit("/");
      verifyExpectedTiles([
        "View data map",
        "View systems",
        "Review privacy requests",
      ]);
    });
  });
});
