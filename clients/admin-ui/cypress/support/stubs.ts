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

export const stubPrivacyRequestsConfigurationCrud = () => {
  cy.intercept("PATCH", "/api/v1/application/settings", {
    fixture: "settings_configuration.json",
  }).as("createConfigurationSettings");

  cy.intercept("GET", "/api/v1/storage/default/*", {
    fixture: "storage_configuration.json",
  }).as("getStorageDetails");

  cy.intercept("PUT", "/api/v1/storage/default", {
    fixture: "storage_configuration.json",
  }).as("createStorage");

  cy.intercept("PUT", "/api/v1/storage/default/*/secret", {
    fixture: "storage_configuration.json",
  }).as("createStorageSecrets");

  cy.intercept("GET", "/api/v1/messaging/default/*", {
    fixture: "messaging_provider_configuration.json",
  }).as("getMessagingConfigurationDetails");

  cy.intercept("PUT", "/api/v1/messaging/default/*", {
    fixture: "messaging_provider_configuration.json",
  }).as("createMessagingConfiguration");

  cy.intercept("PUT", "/api/v1/messaging/default/*/secret", {
    fixture: "messaging_provider_configuration.json",
  }).as("createMessagingConfigurationSecrets");
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

export const stubHomePage = () => {
  cy.intercept("GET", "/api/v1/privacy-request*", {
    statusCode: 200,
    body: { items: [], total: 0, page: 1, size: 25 },
  }).as("getPrivacyRequests");
};
