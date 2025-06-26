import { API_URL } from "../support/constants";

describe("External Manual Tasks - Basic", () => {
  beforeEach(() => {
    // Mock external auth API endpoints
    cy.intercept("POST", `${API_URL}/external-login/request-otp`, {
      body: {
        message: "OTP code sent to email",
        email: "john.doe@example.com",
      },
    }).as("postRequestOtp");

    cy.intercept("POST", `${API_URL}/external-login/verify-otp`, {
      body: {
        user_data: {
          id: "ext_user_123",
          username: "john.doe.external",
          created_at: "2025-06-17T20:17:08.391Z",
          email_address: "john.doe@example.com",
          first_name: "John",
          last_name: "Doe",
          disabled: false,
          disabled_reason: "",
        },
        token_data: {
          access_token: "ext_token_abc123def456",
        },
      },
    }).as("postVerifyOtp");
  });

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

    // Wait for and verify the OTP request API call
    cy.wait("@postRequestOtp").then((interception) => {
      expect(interception.request.body).to.deep.include({
        email: "user@example.com",
        email_token: "test_token_123",
      });
    });

    // Should show verification form after request
    cy.get('[data-testid="otp-verification-form"]').should("be.visible");
    cy.get('[data-testid="otp-input"]').should("be.visible");

    // Step 2: Enter OTP code
    cy.get('[data-testid="otp-input"]').type("123456");
    cy.get('[data-testid="otp-verify-button"]').should("not.be.disabled");
    cy.get('[data-testid="otp-verify-button"]').click();

    // Wait for and verify the OTP verification API call
    cy.wait("@postVerifyOtp").then((interception) => {
      expect(interception.request.body).to.deep.include({
        email: "user@example.com",
        otp_code: "123456",
      });
    });

    // Step 3: Should show authenticated state
    cy.get('[data-testid="external-task-layout"]').should("be.visible");
    cy.contains("Welcome, John!").should("be.visible");
  });
});
