describe("Privacy Request Disclosure", () => {
  describe("footer link visibility", () => {
    it("shows the disclosure link when PRIVACY_REQUEST_DISCLOSURE_ENABLED is true", () => {
      cy.visit("/");
      cy.getByTestId("home");
      cy.overrideSettings({ PRIVACY_REQUEST_DISCLOSURE_ENABLED: true });

      cy.contains("a", "Privacy request disclosures")
        .should("be.visible")
        .and("have.attr", "href", "/privacy-request-metrics");
    });

    it("hides the disclosure link when PRIVACY_REQUEST_DISCLOSURE_ENABLED is false", () => {
      cy.visit("/");
      cy.getByTestId("home");
      cy.overrideSettings({ PRIVACY_REQUEST_DISCLOSURE_ENABLED: false });

      cy.contains("a", "Privacy request disclosures").should("not.exist");
    });

    it("hides the disclosure link by default when setting is not provided", () => {
      cy.visit("/");
      cy.getByTestId("home");

      cy.contains("a", "Privacy request disclosures").should("not.exist");
    });
  });
});
