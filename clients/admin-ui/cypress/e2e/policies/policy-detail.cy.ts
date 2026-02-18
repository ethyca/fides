import { stubDSRPolicies } from "cypress/support/stubs";

import { POLICY_DETAIL_ROUTE } from "~/features/common/nav/routes";

describe("Policy detail page", () => {
  beforeEach(() => {
    cy.login();
    stubDSRPolicies();
    cy.visit(POLICY_DETAIL_ROUTE.replace("[key]", "default_consent_policy"));
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

  it("shows the tabs", () => {
    cy.findByRole("tablist").should("be.visible");
    cy.findByRole("tab", { name: "Rules" }).should("be.visible");
    cy.findByRole("tab", { name: "Conditions" }).should("be.visible");
  });

  it("shows the rules tab", () => {
    cy.getAntTab("Rules").click();
    cy.getAntTabPanel("rules")
      .should("be.visible")
      .within(() => {
        cy.getByTestId("policy-rules-title")
          .should("be.visible")
          .should("have.text", "Policy rules");
        cy.getByTestId("policy-rules-description").should("be.visible");
      });
  });

  it("shows the conditions tab", () => {
    cy.getAntTab("Conditions").click();
    cy.getAntTabPanel("conditions")
      .should("be.visible")
      .within(() => {
        cy.getByTestId("policy-conditions-title")
          .should("be.visible")
          .should("have.text", "Policy conditions");
        cy.getByTestId("policy-conditions-description").should("be.visible");
        cy.getByTestId("policy-conditions-note").should("be.visible");
      });
  });
});
