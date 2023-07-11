import { stubPlus } from "cypress/support/stubs";

import { RoleRegistryEnum } from "~/types/api";

const ALL_TILES = [
  "View data map",
  "Add systems",
  "View systems",
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

  describe("permissions", () => {
    beforeEach(() => {
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
