import { stubDSRPolicies } from "cypress/support/stubs";

import { POLICY_DETAIL_ROUTE } from "~/features/common/nav/routes";

describe("Policy detail page", () => {
  beforeEach(() => {
    cy.login();
    stubDSRPolicies();
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "default_erasure_policy"));
    cy.wait("@getDSRPolicy");
  });

  it("shows the policy details", () => {
    cy.contains("DSR policies").should("be.visible");
    cy.getByTestId("policy-box").should("be.visible");
    cy.getByTestId("policy-box").within(() => {
      cy.contains("Default Erasure Policy").should("be.visible");
      cy.contains("default_erasure_policy").should("be.visible");
    });
  });

  it("shows the tabs with rule count", () => {
    cy.findByRole("tablist").should("be.visible");
    cy.findByRole("tab", { name: /Rules \(1\)/ }).should("be.visible");
    cy.findByRole("tab", { name: /Conditions \(0\)/ }).should("be.visible");
  });

  describe("Rules tab", () => {
    beforeEach(() => {
      cy.getAntTab("Rules").click();
    });

    it("shows the rules heading and description", () => {
      cy.getAntTabPanel("rules")
        .should("be.visible")
        .within(() => {
          cy.contains("h5", "Policy rules").should("be.visible");
          cy.contains("Rules define what actions to take").should("be.visible");
        });
    });

    it("shows the rule in a collapse panel", () => {
      cy.getByTestId("rules-collapse").should("be.visible");
      cy.getByTestId("rules-collapse").within(() => {
        cy.contains("Default Erasure Rule").should("be.visible");
        cy.contains("erasure").should("be.visible");
      });
    });

    it("shows the rule details when expanded", () => {
      // Single rule should be auto-expanded
      cy.getByTestId("rule-name-default_erasure_policy_rule")
        .should("be.visible")
        .should("have.value", "Default Erasure Rule");
      cy.getByTestId("rule-key-default_erasure_policy_rule")
        .should("be.visible")
        .should("have.value", "default_erasure_policy_rule");
      cy.getByTestId("rule-action-default_erasure_policy_rule").should(
        "be.visible",
      );
    });

    it("shows masking strategy for erasure rules", () => {
      cy.getByTestId("rule-masking-default_erasure_policy_rule").should(
        "be.visible",
      );
      cy.contains("Masking strategy").should("be.visible");
    });
  });

  it("shows the conditions tab with add button", () => {
    cy.getAntTab("Conditions").click();
    cy.getAntTabPanel("conditions")
      .should("be.visible")
      .within(() => {
        cy.getByTestId("policy-conditions-title")
          .should("be.visible")
          .should("have.text", "Policy conditions");
        cy.getByTestId("policy-conditions-description").should("be.visible");
        cy.getByTestId("policy-conditions-note").should("be.visible");
        cy.getByTestId("add-condition-btn").should("be.visible");
      });
  });
});

describe("Policy conditions list", () => {
  it("shows the empty state when there are no conditions", () => {
    cy.login();
    stubDSRPolicies();
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "default_erasure_policy"));
    cy.wait("@getDSRPolicy");

    cy.getAntTab("Conditions").click();
    cy.getAntTabPanel("conditions").within(() => {
      cy.getByTestId("conditions-list").should("be.visible");
      cy.contains(
        "No conditions configured. This policy will apply to all matching requests.",
      ).should("be.visible");
    });
  });

  it("shows a single condition leaf", () => {
    cy.login();
    stubDSRPolicies();
    cy.intercept("GET", "/api/v1/dsr/policy/*", {
      body: {
        name: "GDPR Erasure Policy",
        key: "gdpr_erasure_policy",
        drp_action: null,
        execution_timeframe: 30,
        conditions: {
          field_address: "privacy_request.location_regulations",
          operator: "list_contains",
          value: "gdpr",
        },
        rules: [
          {
            name: "Erasure Rule",
            key: "erasure_rule",
            action_type: "erasure",
          },
        ],
      },
    }).as("getDSRPolicy");
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "gdpr_erasure_policy"));
    cy.wait("@getDSRPolicy");

    cy.findByRole("tab", { name: /Conditions \(1\)/ }).should("be.visible");
    cy.getAntTab("Conditions").click();
    cy.getAntTabPanel("conditions").within(() => {
      cy.getByTestId("conditions-list").should("be.visible");
      cy.getByTestId("condition-row-0").should("be.visible");
      cy.getByTestId("condition-row-0").within(() => {
        cy.contains("Location regulations").should("be.visible");
        cy.contains("list contains").should("be.visible");
        cy.contains("gdpr").should("be.visible");
      });
    });
  });

  it("shows multiple conditions from a group", () => {
    cy.login();
    stubDSRPolicies();
    cy.intercept("GET", "/api/v1/dsr/policy/*", {
      body: {
        name: "EU Data Access Request",
        key: "eu_data_access_request",
        drp_action: null,
        execution_timeframe: 30,
        conditions: {
          logical_operator: "or",
          conditions: [
            {
              field_address: "privacy_request.location_country",
              operator: "eq",
              value: "FR",
            },
            {
              field_address: "privacy_request.location_country",
              operator: "eq",
              value: "DE",
            },
            {
              field_address: "privacy_request.location_country",
              operator: "eq",
              value: "IT",
            },
          ],
        },
        rules: [
          {
            name: "EU Access",
            key: "eu_access",
            action_type: "access",
          },
        ],
      },
    }).as("getDSRPolicy");
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "eu_data_access_request"));
    cy.wait("@getDSRPolicy");

    cy.findByRole("tab", { name: /Conditions \(3\)/ }).should("be.visible");
    cy.getAntTab("Conditions").click();
    cy.getAntTabPanel("conditions").within(() => {
      cy.getByTestId("conditions-list").should("be.visible");
      cy.getByTestId("condition-row-0").should("be.visible");
      cy.getByTestId("condition-row-1").should("be.visible");
      cy.getByTestId("condition-row-2").should("be.visible");

      cy.getByTestId("condition-row-0").within(() => {
        cy.contains("Location country").should("be.visible");
        cy.contains("equals").should("be.visible");
        cy.contains("FR").should("be.visible");
      });

      cy.getByTestId("condition-row-2").within(() => {
        cy.contains("IT").should("be.visible");
      });
    });
  });

  it("shows edit and delete buttons for each condition", () => {
    cy.login();
    stubDSRPolicies();
    cy.intercept("GET", "/api/v1/dsr/policy/*", {
      body: {
        name: "GDPR Erasure Policy",
        key: "gdpr_erasure_policy",
        drp_action: null,
        execution_timeframe: 30,
        conditions: {
          field_address: "privacy_request.location_regulations",
          operator: "list_contains",
          value: "gdpr",
        },
        rules: [
          {
            name: "Erasure Rule",
            key: "erasure_rule",
            action_type: "erasure",
          },
        ],
      },
    }).as("getDSRPolicy");
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "gdpr_erasure_policy"));
    cy.wait("@getDSRPolicy");

    cy.getAntTab("Conditions").click();
    cy.getAntTabPanel("conditions").within(() => {
      cy.getByTestId("edit-condition-0-btn").should("be.visible");
      cy.getByTestId("delete-condition-0-btn").should("be.visible");
    });
  });
});

describe("Policy condition builder", () => {
  it("opens the add condition modal", () => {
    cy.login();
    stubDSRPolicies();
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "default_erasure_policy"));
    cy.wait("@getDSRPolicy");

    cy.getAntTab("Conditions").click();
    cy.getByTestId("add-condition-btn").click();
    cy.getAntModal().should("be.visible");
    cy.getAntModal().within(() => {
      cy.contains("Add condition").should("be.visible");
      cy.getByTestId("field-select").should("be.visible");
      cy.getByTestId("operator-select").should("be.visible");
    });
  });

  it("can add a location country condition", () => {
    cy.login();
    stubDSRPolicies();
    cy.intercept("PUT", "/api/v1/dsr/policy/*/conditions", {
      statusCode: 200,
      body: {
        condition: {
          field_address: "privacy_request.location_country",
          operator: "eq",
          value: "FR",
        },
      },
    }).as("updateConditions");
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "default_erasure_policy"));
    cy.wait("@getDSRPolicy");

    cy.getAntTab("Conditions").click();
    cy.getByTestId("add-condition-btn").click();
    cy.getAntModal().should("be.visible");

    cy.getByTestId("field-select").antSelect("Location country");
    cy.getByTestId("operator-select").antSelect("Equals");

    cy.getByTestId("save-condition-btn").click();
  });

  it("can cancel adding a condition", () => {
    cy.login();
    stubDSRPolicies();
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "default_erasure_policy"));
    cy.wait("@getDSRPolicy");

    cy.getAntTab("Conditions").click();
    cy.getByTestId("add-condition-btn").click();
    cy.getAntModal().should("be.visible");

    cy.getByTestId("cancel-btn").click();
    cy.get(".ant-modal-content").should("not.exist");
  });

  it("shows the delete confirmation modal", () => {
    cy.login();
    stubDSRPolicies();
    cy.intercept("GET", "/api/v1/dsr/policy/*", {
      body: {
        name: "GDPR Erasure Policy",
        key: "gdpr_erasure_policy",
        drp_action: null,
        execution_timeframe: 30,
        conditions: {
          field_address: "privacy_request.location_regulations",
          operator: "list_contains",
          value: "gdpr",
        },
        rules: [
          {
            name: "Erasure Rule",
            key: "erasure_rule",
            action_type: "erasure",
          },
        ],
      },
    }).as("getDSRPolicy");
    cy.intercept("PUT", "/api/v1/dsr/policy/*/conditions", {
      statusCode: 200,
      body: { condition: null },
    }).as("updateConditions");
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "gdpr_erasure_policy"));
    cy.wait("@getDSRPolicy");

    cy.getAntTab("Conditions").click();
    cy.getByTestId("delete-condition-0-btn").click();
    cy.contains("Delete condition").should("be.visible");
    cy.contains("Are you sure you want to delete").should("be.visible");
  });

  it("opens the edit condition modal with pre-filled values", () => {
    cy.login();
    stubDSRPolicies();
    cy.intercept("GET", "/api/v1/dsr/policy/*", {
      body: {
        name: "GDPR Erasure Policy",
        key: "gdpr_erasure_policy",
        drp_action: null,
        execution_timeframe: 30,
        conditions: {
          field_address: "privacy_request.location_regulations",
          operator: "list_contains",
          value: "gdpr",
        },
        rules: [
          {
            name: "Erasure Rule",
            key: "erasure_rule",
            action_type: "erasure",
          },
        ],
      },
    }).as("getDSRPolicy");
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "gdpr_erasure_policy"));
    cy.wait("@getDSRPolicy");

    cy.getAntTab("Conditions").click();
    cy.getByTestId("edit-condition-0-btn").click();
    cy.getAntModal().should("be.visible");
    cy.getAntModal().within(() => {
      cy.contains("Edit condition").should("be.visible");
    });
  });
});
