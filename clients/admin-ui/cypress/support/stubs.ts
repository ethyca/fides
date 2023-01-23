import { HealthCheck } from "~/types/api";

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

export const stubDatasetCrud = () => {
  // Dataset editing references taxonomy info, like data categories.
  stubTaxonomyEntities();

  // Create
  cy.intercept("POST", "/api/v1/dataset", { fixture: "dataset.json" }).as(
    "postDataset"
  );

  // Read
  cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
    "getDatasets"
  );
  cy.intercept("GET", "/api/v1/dataset/*", { fixture: "dataset.json" }).as(
    "getDataset"
  );

  // Update
  cy.intercept("PUT", "/api/v1/dataset/*", { fixture: "dataset.json" }).as(
    "putDataset"
  );

  // Delete
  cy.fixture("dataset.json").then((dataset) => {
    cy.intercept("DELETE", "/api/v1/dataset/*", {
      body: {
        message: "resource deleted",
        resource: dataset,
      },
    }).as("deleteDataset");
  });
};

export const CONNECTION_STRING =
  "postgresql://postgres:fidesctl@fidesctl-db:5432/fidesctl_test";

export const stubPlus = (available: boolean, options?: HealthCheck) => {
  if (available) {
    cy.fixture("plus_health.json").then((data) => {
      cy.intercept("GET", "/api/v1/plus/health", {
        statusCode: 200,
        body: options ?? data,
      }).as("getPlusHealth");
    });
  } else {
    cy.intercept("GET", "/api/v1/plus/health", {
      statusCode: 400,
      body: {},
    }).as("getPlusHealth");
  }
};

export const stubHomePage = (hasConnections: boolean, hasSystems: boolean) => {
  if (hasConnections) {
    cy.intercept("GET", "/api/v1/connection?size=5&page=1", {
      fixture: "connections.json",
    }).as("getConnections");
  } else {
    cy.intercept("GET", "/api/v1/connection?size=5&page=1", { body: [] }).as("getConnections");
  }
  if (hasSystems) {
    cy.intercept("GET", "/api/v1/system", { fixture: "systems.json" }).as(
      "getSystems"
    );
  } else {
     cy.intercept("GET", "/api/v1/system", { body: [] }).as("getSystems");
  }
};
