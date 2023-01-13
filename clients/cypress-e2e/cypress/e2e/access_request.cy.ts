import { CREDENTIALS } from "../support/constants";

describe("Access request flow", () => {
  it("can submit an access request from the privacy center", () => {
    // Submit the access request from the privacy center
    cy.visit("localhost:3001");
    cy.getByTestId("card").contains("Access your data").click();
    cy.getByTestId("privacy-request-form").within(() => {
      cy.get("input#name").type("Jenny");
      cy.get("input#email").type("jenny@example.com");

      cy.get("input#phone").type("555 867 5309");
      cy.get("button").contains("Continue").click();
    });

    // Approve the request in the admin UI
    cy.visit("localhost:3000");
    cy.origin("http://localhost:3000", () => {
      cy.login();
    });
  });
});
