describe("Privacy Requests", () => {
  beforeEach(() => {
    cy.login();
  });

  describe("Messaging Provider Configuration", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests/configure/messaging");
    });

    it("Can configure mailgun email as messaging provider", () => {
      cy.getByTestId("option-mailgun-email").click();
    });

    it("Can configure twilio email as messaging provider", () => {
      cy.getByTestId("option-twilio-email").click();
    });

    it("Can configure twilio SMS as messaging provider", () => {
      cy.getByTestId("option-twilio-sms").click();
    });
  });

  describe("Storage Configuration", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests/configure/storage");
    });

    it("Can configure local storage", () => {
      cy.getByTestId("option-local").click();
    });

    it("Can configure S3 storage", () => {
      cy.getByTestId("option-s3").click();
    });
  });
});
