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
    beforeEach(() => {
      cy.visit("/taxonomy");
    });
    it("Can navigate between tabs and load data", () => {
      cy.getByTestId("tab-Data Uses").click();
      cy.wait("@getDataUses");
      cy.getByTestId("tab-Data Subjects").click();
      cy.wait("@getDataSubjects");
      cy.getByTestId("tab-Identifiability").click();
      cy.wait("@getDataQualifiers");
      cy.getByTestId("tab-Data Categories").click();
      cy.wait("@getDataCategories");
    });

    it("Can open up accordion to see taxonomy entities", () => {
      // should only see the 3 root level taxonomy
      cy.getByTestId("accordion-item-Account Data").should("be.visible");
      cy.getByTestId("accordion-item-System Data").should("be.visible");
      cy.getByTestId("accordion-item-User Data").should("be.visible");
      cy.getByTestId("accordion-item-Payment Data").should("not.be.visible");

      // clicking should open up accordions to render more items visible
      cy.getByTestId("accordion-item-Account Data").click();
      cy.getByTestId("accordion-item-Payment Data").should("be.visible");
      cy.getByTestId("accordion-item-Payment Data").click();
      cy.getByTestId("item-Account Payment Financial Account Number").should(
        "be.visible"
      );
    });

    it("Can render accordion elements on flat structures", () => {
      cy.getByTestId("tab-Data Subjects").click();
      cy.getByTestId("item-Anonymous User").should("be.visible");
      cy.getByTestId("item-Shareholder").should("be.visible");
    });

    it("Can render action buttons on hover", () => {
      cy.getByTestId("action-btns").should("not.exist");
      cy.getByTestId("accordion-item-Account Data").trigger("mouseover");
      cy.getByTestId("action-btns").should("exist");
    });
  });
});
