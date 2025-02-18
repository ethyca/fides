import { stubOrganizationCrud } from "cypress/support/stubs";

import { ORGANIZATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

describe("Organization page", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/organization/*", {
      fixture: "organizations/default_organization.json",
    }).as("getOrganization");
  });

  it("can navigate to the Organization page", () => {
    cy.visit("/");
    cy.getByTestId("Settings-nav-group").click();
    cy.getByTestId("Organization-nav-link").click();
    cy.getByTestId("Organization-nav-link").click();
    cy.getByTestId("organization-management");
  });

  describe("can view organization configuration", () => {
    beforeEach(() => {
      cy.visit(ORGANIZATION_MANAGEMENT_ROUTE);
    });

    it("can display a loading state while fetching organization configuration", () => {
      cy.getByTestId("organization-form").within(() => {
        cy.getByTestId("input-fides_key").should(
          "have.value",
          "default_organization",
        );
        cy.getByTestId("input-fides_key").should("be.disabled");
        cy.getByTestId("input-name").should("be.disabled");
        cy.getByTestId("input-description").should("be.empty");
        cy.getByTestId("save-btn").should("be.disabled");
        cy.getByTestId("save-btn").get(".ant-btn-loading-icon");
      });
      cy.wait("@getOrganization");
      cy.getByTestId("input-name").should("be.enabled");
      cy.getByTestId("input-description").should("be.enabled");
    });

    it("can view previously saved organization configuration", () => {
      cy.intercept("GET", "/api/v1/organization/*", {
        fixture: "organizations/complete_organization.json",
      }).as("getOrganization");
      cy.wait("@getOrganization");

      cy.getByTestId("organization-form").within(() => {
        cy.fixture("organizations/complete_organization.json").then(
          (organization) => {
            cy.getByTestId("input-fides_key").should(
              "have.value",
              "default_organization",
            );
            cy.getByTestId("input-fides_key").should("be.disabled");
            cy.getByTestId("input-name").should(
              "have.value",
              organization.name,
            );
            cy.getByTestId("input-description").should(
              "have.value",
              organization.description,
            );
          },
        );
      });
    });
  });

  describe("can edit organization configuration", () => {
    beforeEach(() => {
      stubOrganizationCrud();
      cy.visit(ORGANIZATION_MANAGEMENT_ROUTE);
    });

    it("can edit name & description fields", () => {
      cy.fixture("organizations/edited_organization.json").then(
        (organization) => {
          cy.getByTestId("input-name").clear().type(organization.name);
          cy.getByTestId("input-description")
            .clear()
            .type(organization.description);

          cy.intercept("GET", "/api/v1/organization/*", {
            fixture: "organizations/edited_organization.json",
          });
          cy.getByTestId("save-btn").click();
          cy.wait("@putOrganization").then((interception) => {
            const { body } = interception.request;
            expect(body.name).to.eql(organization.name);
            expect(body.description).to.eql(organization.description);
          });
        },
      );
      cy.getByTestId("toast-success-msg");
    });
  });
});
