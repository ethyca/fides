import { stubMessagingProvidersCrud } from "cypress/support/stubs";

describe("Messaging Providers", () => {
  beforeEach(() => {
    cy.login();
    cy.visit("/");
    stubMessagingProvidersCrud();
  });

  it("Can configure Mailgun email", () => {
    // Navigate directly to Messaging providers page (not in main navigation)
    cy.visit("/notifications/providers");

    // Click the add provider CTA
    cy.getByTestId("add-messaging-provider-btn").click();

    // Select Mailgun from the provider dropdown
    cy.findByLabelText("Provider type").click();
    cy.contains(".ant-select-item", "Mailgun").click();

    // Fill in the domain and API key fields and save
    cy.findByLabelText("Domain").type("test-domain");
    cy.findByLabelText("API key").type("test-api-key");
    cy.getByTestId("save-btn").should("not.be.disabled").click();

    cy.wait("@postMessagingConfig");

    // Expect a success toast for creation
    cy.contains("Mailgun configuration successfully created.");
  });

  it("Can configure Twilio email", () => {
    // Navigate directly to Messaging providers page (not in main navigation)
    cy.visit("/notifications/providers");
    cy.getByTestId("add-messaging-provider-btn").click();

    // Select Twilio Email
    cy.findByLabelText("Provider type").click();
    cy.contains(".ant-select-item", "Twilio email").click();

    // Fill and save
    cy.findByLabelText("Email").type("test@example.com");
    cy.findByLabelText("API key").type("twilio-api-key");
    cy.getByTestId("save-btn").should("not.be.disabled").click();
    cy.wait("@postMessagingConfig");

    // Expect a success toast for creation
    cy.contains("Twilio email configuration successfully created.");
  });

  it("Can configure Twilio SMS", () => {
    // Navigate directly to Messaging providers page (not in main navigation)
    cy.visit("/notifications/providers");
    cy.getByTestId("add-messaging-provider-btn").click();

    // Select Twilio SMS
    cy.findByLabelText("Provider type").click();
    cy.contains(".ant-select-item", "Twilio SMS").click();

    // Fill and save
    cy.findByLabelText("Account SID").type("ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx");
    cy.findByLabelText("Auth token").type("auth-token-value");
    // satisfy validation: either Messaging service SID or Phone number
    cy.findByLabelText("Messaging service SID").type(
      "MGxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    );
    cy.getByTestId("save-btn").should("not.be.disabled").click();
    cy.wait("@postMessagingConfig");

    // Expect a success toast for creation
    cy.contains("Twilio SMS configuration successfully created.");
  });
});
