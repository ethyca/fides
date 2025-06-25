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
      .and("contain", "Send Verification Code");
  });

  it("should have proper page title", () => {
    cy.visit("/manual-tasks-external?token=test_token_123");
    cy.contains("External Manual Tasks").should("be.visible");
  });

  it("should complete the OTP authentication flow", () => {
    cy.visit("/manual-tasks-external?token=test_token_123");

    // Step 1: Request OTP
    cy.get('[data-testid="otp-request-button"]').click();

    // Should show verification form after request
    cy.get('[data-testid="otp-verification-form"]').should("be.visible");
    cy.get('[data-testid="otp-input"]').should("be.visible");

    // Step 2: Enter OTP code
    cy.get('[data-testid="otp-input"]').type("123456");
    cy.get('[data-testid="otp-verify-button"]').should("not.be.disabled");
    cy.get('[data-testid="otp-verify-button"]').click();

    // Step 3: Should show authenticated state
    cy.get('[data-testid="external-task-layout"]').should("be.visible");
    cy.contains("Welcome, John!").should("be.visible");
  });
});
