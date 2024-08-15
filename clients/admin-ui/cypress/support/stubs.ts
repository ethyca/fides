import { PrivacyRequestResponse } from "~/features/privacy-requests/types";
import { HealthCheck } from "~/types/api";

export const stubTaxonomyEntities = () => {
  cy.intercept("GET", "/api/v1/data_category", {
    fixture: "taxonomy/data_categories.json",
  }).as("getDataCategories");
  cy.intercept("GET", "/api/v1/data_subject", {
    fixture: "taxonomy/data_subjects.json",
  }).as("getDataSubjects");
  cy.intercept("GET", "/api/v1/data_use", {
    fixture: "taxonomy/data_uses.json",
  }).as("getDataUses");
};

export const stubLanguages = () => {
  cy.intercept("GET", "/api/v1/plus/languages*", {
    fixture: "languages.json",
  }).as("getLanguages");
};

export const stubSystemCrud = () => {
  cy.intercept("POST", "/api/v1/system", {
    fixture: "systems/system.json",
  }).as("postSystem");
  cy.intercept("GET", "/api/v1/system/*", {
    fixture: "systems/system.json",
  }).as("getSystem");
  cy.intercept("PUT", "/api/v1/system*", { fixture: "systems/system.json" }).as(
    "putSystem",
  );
  cy.fixture("systems/system.json").then((system) => {
    cy.intercept("DELETE", "/api/v1/system/*", {
      body: {
        message: "resource deleted",
        resource: system,
      },
    }).as("deleteSystem");
  });
};

export const stubVendorList = () => {
  cy.intercept("GET", "/api/v1/plus/dictionary/system*", {
    fixture: "dictionary-entries.json",
  }).as("getDictionaryEntries");
  cy.intercept("GET", "/api/v1/plus/dictionary/data-use-declarations/*", {
    fixture: "dictionary-declarations.json",
  }).as("getDictionaryDeclarations");
};

export const stubOrganizationCrud = () => {
  cy.intercept("POST", "/api/v1/organization", {
    fixture: "organizations/default_organization.json",
  }).as("postOrganization");
  cy.intercept("GET", "/api/v1/organization/*", {
    fixture: "organizations/default_organization.json",
  }).as("getOrganization");
  cy.intercept("PUT", "/api/v1/organization*", {
    fixture: "organizations/default_organization.json",
  }).as("putOrganization");
  cy.fixture("organizations/default_organization.json").then((organization) => {
    cy.intercept("DELETE", "/api/v1/organization/*", {
      body: {
        message: "resource deleted",
        resource: organization,
      },
    }).as("deleteOrganization");
  });
};

export const stubDatasetCrud = () => {
  // Dataset editing references taxonomy info, like data categories.
  stubTaxonomyEntities();

  // Create
  cy.intercept("POST", "/api/v1/dataset", { fixture: "dataset.json" }).as(
    "postDataset",
  );

  // Read
  cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
    "getDatasets",
  );
  cy.intercept("GET", "/api/v1/dataset?page*", {
    fixture: "datasets_paginated.json",
  }).as("getFilteredDatasets");

  cy.intercept("GET", "/api/v1/dataset/*", { fixture: "dataset.json" }).as(
    "getDataset",
  );

  // Update
  cy.intercept("PUT", "/api/v1/dataset*", { fixture: "dataset.json" }).as(
    "putDataset",
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
  cy.intercept("PATCH", "/api/v1/config", {
    fixture: "/privacy-requests/settings_configuration.json",
  }).as("createConfigurationSettings");

  cy.intercept("GET", "/api/v1/storage/default/*", {
    fixture: "/privacy-requests/settings_configuration.json",
  }).as("getStorageDetails");

  cy.intercept("PUT", "/api/v1/storage/default", {
    fixture: "/privacy-requests/settings_configuration.json",
  }).as("createStorage");

  cy.intercept("PUT", "/api/v1/storage/default/*/secret", {
    fixture: "/privacy-requests/settings_configuration.json",
  }).as("createStorageSecrets");

  cy.intercept("PUT", "/api/v1/messaging/default", {
    fixture: "/privacy-requests/messaging_configuration.json",
  }).as("createMessagingConfiguration");

  cy.intercept("GET", "/api/v1/plus/privacy-center-config", {
    fixture: "/privacy-requests/privacy-center-config.json",
  }).as("getPrivacyCenterConfig");
};

export const stubPrivacyNoticesCrud = () => {
  cy.intercept("GET", "/api/v1/privacy-notice*", {
    fixture: "privacy-notices/list.json",
  }).as("getNotices");
  cy.intercept("GET", "/api/v1/privacy-notice/pri*", {
    fixture: "privacy-notices/notice.json",
  }).as("getNoticeDetail");
  cy.intercept("POST", "/api/v1/privacy-notice", {
    fixture: "privacy-notices/list.json",
  }).as("postNotices");
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
  }).as("getHomePagePrivacyRequests");
};

export const stubPrivacyRequests = () => {
  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/privacy-request",
      /**
       * Query parameters could also match fixtures more specifically:
       * https://docs.cypress.io/api/commands/intercept#Icon-nameangle-right--routeMatcher-RouteMatcher
       */
      query: {
        include_identities: "true",
        page: "*",
        size: "*",
      },
    },
    { fixture: "privacy-requests/list.json" },
  ).as("getPrivacyRequests");

  cy.fixture("privacy-requests/list.json").then(
    (privacyRequests: PrivacyRequestResponse) => {
      const privacyRequest = privacyRequests.items[0];

      // This lets us use `cy.get("@privacyRequest")` as a shorthand for getting the singular
      // privacy request object.
      cy.wrap(privacyRequest).as("privacyRequest");

      cy.intercept(
        {
          method: "GET",
          pathname: "/api/v1/privacy-request",
          query: {
            include_identities: "true",
            request_id: privacyRequest.id,
          },
        },
        {
          body: {
            items: [privacyRequest],
            total: 1,
          },
        },
      ).as("getPrivacyRequest");
    },
  );

  cy.intercept(
    {
      method: "PATCH",
      pathname: "/api/v1/privacy-request/administrate/approve",
    },
    {
      fixture: "privacy-requests/approve.json",
    },
  ).as("approvePrivacyRequest");

  cy.intercept(
    {
      method: "PATCH",
      pathname: "/api/v1/privacy-request/administrate/deny",
    },
    {
      fixture: "privacy-requests/deny.json",
    },
  ).as("denyPrivacyRequest");
};

export const stubDatamap = () => {
  cy.intercept("GET", "/api/v1/plus/datamap/*", {
    fixture: "datamap/datamap.json",
  }).as("getDatamap");
  cy.intercept("GET", "/api/v1/data_category", {
    fixture: "taxonomy/data_categories.json",
  }).as("getDataCategory");
  cy.intercept("GET", "/api/v1/system", { fixture: "systems/systems.json" }).as(
    "getSystems",
  );
};

export const stubLocations = () => {
  cy.intercept("GET", "/api/v1/plus/locations", {
    fixture: "locations/list.json",
  }).as("getLocations");
  cy.intercept("PATCH", "/api/v1/plus/locations", {
    fixture: "locations/list.json",
  }).as("patchLocations");
};

export const stubSystemVendors = () => {
  cy.intercept("GET", "/api/v1/plus/dictionary/system-vendors", {
    fixture: "systems/system-vendors.json",
  }).as("getSystemVendors");
};

export const stubTranslationConfig = (enabled: boolean) => {
  cy.intercept("GET", "/api/v1/config*", {
    body: {
      plus_consent_settings: {
        enable_translations: enabled,
        enable_oob_translations: enabled,
      },
    },
  }).as("getTranslationConfig");
};

export const stubStagedResourceActions = () => {
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/**/confirm*").as(
    "confirmResource",
  );
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/mute*").as(
    "ignoreResource",
  );
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/promote*").as(
    "promoteResource",
  );
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/un-mute*").as(
    "unmuteResource",
  );
};
