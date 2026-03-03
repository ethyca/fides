import { stubDSRPolicies } from "cypress/support/stubs";

import {
  POLICIES_ROUTE,
  POLICY_DETAIL_ROUTE,
} from "~/features/common/nav/routes";

describe("Policy CRUD", () => {
  describe("Create policy", () => {
    beforeEach(() => {
      cy.login();
      stubDSRPolicies();
      cy.visit(POLICIES_ROUTE);
      cy.wait("@getDSRPolicies");
    });

    it("shows the create policy button", () => {
      cy.getByTestId("create-policy-btn").should("be.visible");
    });

    it("opens the create policy modal", () => {
      cy.getByTestId("create-policy-btn").click();
      cy.getAntModalHeader().contains("Create policy").should("be.visible");
      cy.getByTestId("policy-name-input").should("be.visible");
      cy.getByTestId("policy-key-input").should("be.visible");
      cy.getByTestId("policy-timeframe-input").should("be.visible");
    });

    it("auto-generates the key from the name", () => {
      cy.getByTestId("create-policy-btn").click();
      cy.getByTestId("policy-name-input").type("My Test Policy");
      cy.getByTestId("policy-key-input").should("have.value", "my_test_policy");
    });

    it("submits the form and calls PATCH", () => {
      cy.getByTestId("create-policy-btn").click();
      cy.getByTestId("policy-name-input").type("Test Policy");

      cy.getAntModalFooter().contains("Create").click();
      cy.wait("@patchDSRPolicy");
    });

    it("shows validation error when name is empty", () => {
      cy.getByTestId("create-policy-btn").click();
      cy.getAntModalFooter().contains("Create").click();
      cy.contains("Name is required").should("be.visible");
    });
  });

  describe("Edit policy", () => {
    beforeEach(() => {
      cy.login();
      stubDSRPolicies();
      cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "default_erasure_policy"));
      cy.wait("@getDSRPolicy");
    });

    it("shows edit and delete buttons on detail page", () => {
      cy.getByTestId("edit-policy-btn").should("be.visible");
      cy.getByTestId("delete-policy-btn").should("be.visible");
    });

    it("opens edit modal with pre-populated fields", () => {
      cy.getByTestId("edit-policy-btn").click();
      cy.getAntModalHeader().contains("Edit policy").should("be.visible");
      cy.getByTestId("policy-name-input").should(
        "have.value",
        "Default Erasure Policy",
      );
      cy.getByTestId("policy-key-input").should(
        "have.value",
        "default_erasure_policy",
      );
    });

    it("disables the key field when editing", () => {
      cy.getByTestId("edit-policy-btn").click();
      cy.getByTestId("policy-key-input").should("be.disabled");
    });

    it("submits the edit form and calls PATCH", () => {
      cy.getByTestId("edit-policy-btn").click();
      cy.getByTestId("policy-name-input").clear().type("Updated Policy");
      cy.getAntModalFooter().contains("Save").click();
      cy.wait("@patchDSRPolicy");
    });
  });

  describe("Delete policy from list page", () => {
    beforeEach(() => {
      cy.login();
      stubDSRPolicies();
      cy.visit(POLICIES_ROUTE);
      cy.wait("@getDSRPolicies");
    });

    it("shows delete button on each policy row", () => {
      cy.getByTestId("delete-policy-custom_erasure_policy-btn").should(
        "be.visible",
      );
    });

    it("opens delete confirmation modal", () => {
      cy.getByTestId("delete-policy-custom_erasure_policy-btn").click();
      cy.getAntModal().should("be.visible");
      cy.contains("Are you sure you want to delete").should("be.visible");
      cy.contains("Custom Erasure Policy").should("be.visible");
      cy.getAntModalConfirmButtons().contains("Delete").click();
      cy.wait("@deleteDSRPolicy");
    });

    it("cancels delete without calling API", () => {
      cy.getByTestId("delete-policy-custom_erasure_policy-btn").click();
      cy.getAntModalConfirmButtons().contains("Cancel").click();
      cy.getAntModal().should("not.exist");
    });
  });

  describe("Delete policy from detail page", () => {
    it("disables delete button on default policy detail page", () => {
      cy.login();
      stubDSRPolicies();
      cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "default_erasure_policy"));
      cy.wait("@getDSRPolicy");

      cy.getByTestId("delete-policy-btn").should("be.disabled");
    });

    it("opens delete confirmation modal for non-default policy", () => {
      cy.login();
      stubDSRPolicies();
      cy.intercept("GET", "/api/v1/dsr/policy/*", {
        body: {
          name: "Custom Erasure Policy",
          key: "custom_erasure_policy",
          drp_action: "deletion",
          execution_timeframe: 30,
          rules: [
            {
              name: "Custom Erasure Rule",
              key: "custom_erasure_rule",
              action_type: "erasure",
              storage_destination: null,
              masking_strategy: {
                strategy: "null_rewrite",
              },
            },
          ],
        },
      }).as("getDSRPolicy");
      cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "custom_erasure_policy"));
      cy.wait("@getDSRPolicy");

      cy.getByTestId("delete-policy-btn").should("not.be.disabled");
      cy.getByTestId("delete-policy-btn").click();
      cy.contains("Delete policy").should("be.visible");
      cy.contains("Are you sure you want to delete").should("be.visible");
      cy.getAntModalConfirmButtons().contains("Delete").click();
      cy.wait("@deleteDSRPolicy");
    });
  });
});
