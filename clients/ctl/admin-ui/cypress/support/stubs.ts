export const stubTaxonomyEntities = () => {
  cy.intercept("GET", "/api/v1/data_category", {
    fixture: "data_categories.json",
  }).as("getDataCategory");
  cy.intercept("GET", "/api/v1/data_qualifier", {
    fixture: "data_qualifiers.json",
  }).as("getDataQualifier");
  cy.intercept("GET", "/api/v1/data_subject", {
    fixture: "data_subjects.json",
  }).as("getDataSubject");
  cy.intercept("GET", "/api/v1/data_use", {
    fixture: "data_uses.json",
  }).as("getDataUse");
};

export const stubSystemCrud = () => {
  cy.intercept("POST", "/api/v1/system", { fixture: "system.json" }).as(
    "postSystem"
  );
  cy.intercept("GET", "/api/v1/system/*", { fixture: "system.json" }).as(
    "getSystem"
  );
  cy.intercept("PUT", "/api/v1/system*", { fixture: "system.json" }).as(
    "putSystem"
  );
  cy.fixture("system.json").then((system) => {
    cy.intercept("DELETE", "/api/v1/system/*", {
      body: {
        message: "resource deleted",
        resource: system,
      },
    }).as("deleteSystem");
  });
};
