/**
 * Regression test for ENG-3137: Viewer user can't edit a system assigned to them
 *
 * A viewer user with an assigned system should be able to edit that system.
 * The RBAC commit (8e9788e) introduced a read-only check that only looks at
 * the global SYSTEM_UPDATE scope, ignoring SYSTEM_MANAGER_UPDATE which
 * allows per-system editing for assigned systems.
 */
import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/routes";
import { RoleRegistryEnum, ScopeRegistryEnum } from "~/types/api";

describe("ENG-3137: Viewer with assigned system should be able to edit", () => {
  beforeEach(() => {
    cy.login();
    cy.overrideFeatureFlag("alphaRbac", true);
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
  });

  it("viewer with system_manager:update can edit assigned system", () => {
    // Simulate a viewer who also has system_manager:update for their assigned system
    cy.fixture("login.json").then((body) => {
      const { id: userId } = body.user_data;
      cy.intercept(`/api/v1/user/${userId}/permission`, {
        body: {
          id: userId,
          user_id: userId,
          roles: [RoleRegistryEnum.VIEWER],
          total_scopes: [
            // Standard viewer scopes
            ScopeRegistryEnum.SYSTEM_READ,
            ScopeRegistryEnum.SYSTEM_MANAGER_READ,
            ScopeRegistryEnum.SYSTEM_MANAGER_UPDATE,
            // Other viewer scopes
            ScopeRegistryEnum.USER_READ,
            ScopeRegistryEnum.ORGANIZATION_READ,
          ],
        },
      }).as("getUserPermission");
    });

    cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system`);
    cy.wait("@getUserPermission");

    // The form should NOT be read-only for a viewer with system_manager:update
    cy.getByTestId("input-name").should("exist");

    // Regression guard (ENG-3137): read-only alert should NOT appear
    cy.contains("Read-only access").should("not.exist");

    // Regression guard (ENG-3137): form fields should be editable, not disabled
    cy.get("fieldset[disabled]").should("not.exist");
  });

  it("viewer WITHOUT system_manager:update sees read-only form", () => {
    // Standard viewer without system_manager:update
    cy.assumeRole(RoleRegistryEnum.VIEWER);

    cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system`);

    cy.getByTestId("input-name").should("exist");

    // This viewer SHOULD see read-only since they have no update permissions
    cy.contains("Read-only access").should("exist");
    cy.get("fieldset[disabled]").should("exist");
  });
});
