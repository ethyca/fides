import { stubDSRPolicies } from "cypress/support/stubs";

import { POLICIES_ROUTE } from "~/features/common/nav/routes";

describe("Policies list page", () => {
  describe("policy list display", () => {
    beforeEach(() => {
      cy.login();
      stubDSRPolicies();
      cy.visit(POLICIES_ROUTE);
      cy.wait("@getDSRPolicies");
    });

    it("shows page heading and description", () => {
      cy.contains("DSR policies").should("be.visible");
      cy.contains(
        "DSR policies define how privacy requests are processed",
      ).should("be.visible");
    });

    it("renders all policies in the list", () => {
      cy.getByTestId("policies-list").should("exist");
      cy.contains("Default Consent Policy").should("be.visible");
      cy.contains("Default Erasure Policy").should("be.visible");
      cy.contains("Default Access Policy").should("be.visible");
    });

    it("displays the policy key for each policy", () => {
      cy.contains("default_consent_policy").should("be.visible");
      cy.contains("default_erasure_policy").should("be.visible");
      cy.contains("default_access_policy").should("be.visible");
    });

    it("displays execution timeframe for each policy", () => {
      cy.contains("45 days").should("exist");
    });

    it("displays action type tags from policy rules", () => {
      cy.contains("Default Consent Policy")
        .closest("li")
        .within(() => {
          cy.contains("consent").should("exist");
        });
      cy.contains("Default Erasure Policy")
        .closest("li")
        .within(() => {
          cy.contains("erasure").should("exist");
        });
      cy.contains("Default Access Policy")
        .closest("li")
        .within(() => {
          cy.contains("access").should("exist");
        });
    });
  });

  describe("search and filter", () => {
    beforeEach(() => {
      cy.login();
      stubDSRPolicies();
      cy.visit(POLICIES_ROUTE);
      cy.wait("@getDSRPolicies");
    });

    it("filters policies by name when typing in search", () => {
      cy.getByTestId("search-bar").type("Consent");
      cy.contains("Default Consent Policy").should("be.visible");
      cy.contains("Default Erasure Policy").should("not.exist");
      cy.contains("Default Access Policy").should("not.exist");
    });

    it("filters policies by key when typing in search", () => {
      cy.getByTestId("search-bar").type("default_erasure");
      cy.contains("Default Erasure Policy").should("be.visible");
      cy.contains("Default Consent Policy").should("not.exist");
      cy.contains("Default Access Policy").should("not.exist");
    });

    it("shows empty state when search has no matches", () => {
      cy.getByTestId("search-bar").type("nonexistent policy xyz");
      cy.contains("No policies match your search").should("be.visible");
    });

    it("is not case sensitive", () => {
      cy.getByTestId("search-bar").type("consent");
      cy.contains("Default Consent Policy").should("be.visible");
    });
  });

  describe("default policy delete protection", () => {
    beforeEach(() => {
      cy.login();
      stubDSRPolicies();
      cy.visit(POLICIES_ROUTE);
      cy.wait("@getDSRPolicies");
    });

    it("disables delete button on default policies", () => {
      cy.getByTestId("delete-policy-default_consent_policy-btn").should(
        "be.disabled",
      );
      cy.getByTestId("delete-policy-default_erasure_policy-btn").should(
        "be.disabled",
      );
      cy.getByTestId("delete-policy-default_access_policy-btn").should(
        "be.disabled",
      );
    });

    it("enables delete button on non-default policies", () => {
      cy.getByTestId("delete-policy-custom_erasure_policy-btn").should(
        "not.be.disabled",
      );
    });

    it("shows tooltip on hover of disabled default policy delete button", () => {
      cy.getByTestId("delete-policy-default_consent_policy-btn").trigger(
        "mouseover",
      );
      cy.contains("Default policies cannot be deleted").should("be.visible");
    });
  });

  describe("empty state", () => {
    it("shows empty message when no policies exist", () => {
      cy.login();
      stubDSRPolicies({ isEmpty: true });
      cy.visit(POLICIES_ROUTE);
      cy.wait("@getDSRPolicies");

      cy.contains("No policies configured").should("be.visible");
    });
  });
});
