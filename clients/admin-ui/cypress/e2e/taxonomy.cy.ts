describe("Taxonomy management page", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/data_category", {
      fixture: "data_categories.json",
    }).as("getDataCategories");
    cy.intercept("GET", "/api/v1/data_use", { fixture: "data_uses.json" }).as(
      "getDataUses"
    );
    cy.intercept("GET", "/api/v1/data_subject", {
      fixture: "data_subjects.json",
    }).as("getDataSubjects");
    cy.intercept("GET", "/api/v1/data_qualifier", {
      fixture: "data_qualifiers.json",
    }).as("getDataQualifiers");
  });

  it("Can navigate to the taxonomy page", () => {
    cy.visit("/");
    cy.getByTestId("nav-link-Taxonomy").click();
    cy.getByTestId("taxonomy-tabs");
    cy.getByTestId("tab-Data Categories");
    cy.getByTestId("tab-Data Uses");
    cy.getByTestId("tab-Data Subjects");
    cy.getByTestId("tab-Identifiability");
  });

  describe("Can view data", () => {
    it("Can navigate between tabs and load data", () => {
      cy.visit("/taxonomy");
      cy.getByTestId("tab-Data Uses").click();
      cy.wait("@getDataUses");
      cy.getByTestId("tab-Data Subjects").click();
      cy.wait("@getDataSubjects");
      cy.getByTestId("tab-Identifiability").click();
      cy.wait("@getDataQualifiers");
      cy.getByTestId("tab-Data Categories").click();
      cy.wait("@getDataCategories");
    });
  });
});
