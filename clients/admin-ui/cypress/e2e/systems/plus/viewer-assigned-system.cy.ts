import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/routes";
import { RoleRegistryEnum } from "~/types/api";

const ASSIGNED_SYSTEM_KEY = "demo_analytics_system";

describe("Viewer with assigned system on the System Information form", () => {
  beforeEach(() => {
    cy.login();
    stubSystemCrud();
    stubTaxonomyEntities();
    stubPlus(true, {
      core_fides_version: "2.2.0",
      fidesplus_server: "healthy",
      fidesplus_version: "2.2.0",
      dictionary: { enabled: true, service_health: null, service_error: null },
      fides_cloud: { enabled: true },
      rbac: { enabled: true },
      tcf: { enabled: true },
    });
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

  it("viewer assigned to this system can edit it", () => {
    cy.assumeRole(RoleRegistryEnum.VIEWER);

    cy.fixture("login.json").then((body) => {
      const { id: userId } = body.user_data;
      cy.fixture("systems/systems.json").then((systems) => {
        const assignedSystem = systems.find(
          (s: { fides_key: string }) => s.fides_key === ASSIGNED_SYSTEM_KEY,
        );
        cy.intercept(`/api/v1/user/${userId}/system-manager`, {
          body: [assignedSystem],
        }).as("getManagedSystems");
      });
    });

    cy.visit(`${SYSTEM_ROUTE}/configure/${ASSIGNED_SYSTEM_KEY}`);
    cy.wait("@getManagedSystems");

    cy.getByTestId("input-name").should("exist");
    cy.contains("Read-only access").should("not.exist");
    cy.get("fieldset[disabled]").should("not.exist");
  });

  it("viewer NOT assigned to this system sees read-only form", () => {
    cy.assumeRole(RoleRegistryEnum.VIEWER);

    cy.fixture("login.json").then((body) => {
      const { id: userId } = body.user_data;
      cy.intercept(`/api/v1/user/${userId}/system-manager`, {
        body: [],
      }).as("getManagedSystems");
    });

    cy.visit(`${SYSTEM_ROUTE}/configure/${ASSIGNED_SYSTEM_KEY}`);
    cy.wait("@getManagedSystems");

    cy.getByTestId("input-name").should("exist");
    cy.contains("Read-only access").should("exist");
    cy.get("fieldset[disabled]").should("exist");
  });
});
