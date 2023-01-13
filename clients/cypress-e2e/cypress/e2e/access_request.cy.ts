describe("Access request flow", () => {
  it("can submit an access request from the privacy center", () => {
    // Watch these routes without changing or stubbing its response
    cy.intercept(
      "PATCH",
      "http://0.0.0.0:8080/api/v1/privacy-request/administrate/approve"
    ).as("patchRequest");
    cy.intercept("GET", "http://0.0.0.0:8080/api/v1/privacy-request*").as(
      "getRequests"
    );

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
      cy.get("div").contains("Review privacy requests").click();
      let numCompletedRequests = 0;
      cy.wait("@getRequests").then((interception) => {
        const { items } = interception.response.body;
        numCompletedRequests = items.filter(
          (i) => i.status === "complete"
        ).length;
      });

      cy.getByTestId("privacy-request-row-pending")
        .first()
        .trigger("mouseover")
        .get("button")
        .contains("Approve")
        .click();

      cy.wait("@patchRequest");
      cy.wait("@getRequests");

      // Make sure there is one more completed request than originally
      cy.getByTestId("privacy-request-row-complete").then((rows) => {
        expect(rows.length).to.eql(numCompletedRequests + 1);
      });
    });
  });
});
