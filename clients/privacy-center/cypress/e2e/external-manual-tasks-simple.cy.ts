describe("External Manual Tasks - Basic", () => {
  it("should load the external manual tasks page", () => {
    cy.visit("/manual-tasks-external?token=test_token_123");

    // Should show the basic page structure
    cy.get('[data-testid="external-auth-container"]').should("be.visible");
    cy.get('[data-testid="otp-request-form"]').should("be.visible");

    // Should display the token
    cy.contains("Token: test_token_123").should("be.visible");

    // Should show the OTP request elements
    cy.get('[data-testid="otp-request-email-display"]')
      .should("be.visible")
      .and("contain", "user@example.com");

    cy.get('[data-testid="otp-request-button"]')
      .should("be.visible")
      .and("contain", "Send OTP");
  });

  it("should have proper page title", () => {
    cy.visit("/manual-tasks-external?token=test_token_123");
    cy.contains("External Manual Tasks").should("be.visible");
  });
});
