import {
  stubDatasetCrud,
  stubPlus,
  stubSystemAssets,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
  stubVendorList,
} from "cypress/support/stubs";

import { ADD_SYSTEMS_MANUAL_ROUTE } from "~/features/common/nav/routes";

describe("System Information Tab", () => {
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
    cy.intercept("/api/v1/config?api_set=false", {});
    stubDatasetCrud();
    stubSystemIntegrations();
    stubSystemVendors();
    stubVendorList();
    stubSystemAssets();
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

  it("locks editing for some GVL vendor fields when TCF is enabled", () => {
    cy.getByTestId("vendor-name-select").find("input").type("Aniview");
    cy.getByTestId("vendor-name-select").antSelect("Aniview LTD");

    cy.getByTestId("locked-for-GVL-notice");
    cy.getByTestId("input-description").should("not.be.disabled");
    cy.getByTestId("controlled-select-tags")
      .find("input")
      .should("not.be.disabled");
    cy.getByTestId("input-legal_name").should("not.be.disabled");
    cy.getByTestId("input-legal_address").should("not.be.disabled");
    cy.getByTestId("input-administrating_department").should("not.be.disabled");
    cy.getByTestId("controlled-select-responsibility")
      .find("input")
      .should("not.be.disabled");
    cy.getByTestId("input-joint_controller_info").should("not.be.disabled");
    cy.getByTestId("input-data_security_practices").should("not.be.disabled");
    cy.getByTestId("input-reason_for_exemption").should("be.disabled");
  });

  it("does not lock editing for a non-GVL vendor", () => {
    cy.getByTestId("vendor-name-select").find("input").type("L{enter}");

    cy.getByTestId("locked-for-GVL-notice").should("not.exist");
    cy.getByTestId("input-description").should("not.be.disabled");
    cy.getByTestId("controlled-select-tags")
      .find("input")
      .should("not.be.disabled");
    cy.getByTestId("input-legal_name").should("not.be.disabled");
    cy.getByTestId("input-legal_address").should("not.be.disabled");
    cy.getByTestId("input-administrating_department").should("not.be.disabled");
    cy.getByTestId("controlled-select-responsibility")
      .find("input")
      .should("not.be.disabled");
    cy.getByTestId("input-joint_controller_info").should("not.be.disabled");
    cy.getByTestId("input-data_security_practices").should("not.be.disabled");
    cy.getByTestId("input-reason_for_exemption").should("not.be.disabled");
  });

  it("locks editing some fields and changing name for a GVL vendor when visiting 'edit system' page directly", () => {
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
    cy.getByTestId("input-description").should("not.be.disabled");
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
});
