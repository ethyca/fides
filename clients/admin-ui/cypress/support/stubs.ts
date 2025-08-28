import { PrivacyRequestResponse } from "~/features/privacy-requests/types";
import { HealthCheck, PrivacyRequestStatus } from "~/types/api";

export const stubTaxonomyEntities = () => {
  cy.intercept("GET", "/api/v1/data_category", {
    fixture: "taxonomy/data_categories.json",
  }).as("getDataCategories");
  cy.intercept("PUT", "/api/v1/data_category*", {}).as("putDataCategories");
  cy.intercept("GET", "/api/v1/data_subject", {
    fixture: "taxonomy/data_subjects.json",
  }).as("getDataSubjects");
  cy.intercept("GET", "/api/v1/data_use", {
    fixture: "taxonomy/data_uses.json",
  }).as("getDataUses");
  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/plus/custom-metadata/allow-list",
      query: {
        show_values: "true",
      },
    },
    {
      fixture: "taxonomy/custom-metadata/allow-list/list.json",
    },
  ).as("getAllowLists");
  cy.intercept(
    "GET",
    `/api/v1/plus/custom-metadata/custom-field-definition/resource-type/*`,

    {
      body: {
        detail: "No custom metadata fields found with resource type system",
      },
    },
  ).as("getCustomFieldDefinitions");
  cy.intercept("GET", `/api/v1/plus/custom-metadata/custom-field/resource/*`, {
    fixture: "taxonomy/custom-metadata/custom-field/list.json",
  }).as("getCustomFields");
  cy.intercept("GET", `/api/v1/plus/custom-metadata/custom-field/resource`, {
    fixture: "taxonomy/custom-metadata/custom-field/list.json",
  }).as("getCustomFields");
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
  cy.intercept("GET", "/api/v1/system", {
    fixture: "systems/systems.json",
  }).as("getSystems");
  cy.intercept("GET", "/api/v1/system/*", {
    fixture: "systems/system.json",
  }).as("getSystem");
  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/system",
      query: {
        page: "*",
        size: "*",
      },
    },
    {
      fixture: "systems/systems_paginated.json",
    },
  ).as("getSystemsPaginated");
  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/system",
      query: {
        page: "*",
        size: "*",
        search: "demo m",
      },
    },
    {
      fixture: "systems/systems_paginated_search.json",
    },
  ).as("getSystemsWithSearch");
  cy.intercept("PUT", "/api/v1/system*", {
    fixture: "systems/system.json",
  }).as("putSystem");
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
  cy.intercept("GET", "/api/v1/dataset?minimal=true", {
    fixture: "connectors/minimal_datasets.json",
  }).as("getMinimalDatasets");
  cy.intercept("GET", "/api/v1/dataset?page*", {
    fixture: "datasets_paginated.json",
  }).as("getFilteredDatasets");
  cy.intercept("GET", "/api/v1/dataset?page*&minimal=true", {
    fixture: "datasets_paginated_minimal.json",
  }).as("getFilteredMinimalDatasets");

  cy.intercept("GET", "/api/v1/dataset/*", { fixture: "dataset.json" }).as(
    "getDataset",
  );

  cy.intercept("GET", "/api/v1/dataset?only_unlinked_datasets=false", []).as(
    "getUnlinkedDatasets",
  );
  cy.intercept(
    "GET",
    "/api/v1/dataset?only_unlinked_datasets=false&minimal=true",
    { fixture: "connectors/minimal_datasets.json" },
  ).as("getMinimalUnlinkedDatasets");

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

  // Filtered
  cy.intercept("GET", "/api/v1/filter/dataset*", {
    fixture: "datasets.json",
  }).as("getFilteredDatasets");
};

export const stubPrivacyRequestsConfigurationCrud = () => {
  cy.intercept("PATCH", "/api/v1/config", {
    fixture: "/privacy-requests/settings_configuration.json",
  }).as("createConfigurationSettings");

  cy.intercept("GET", "/api/v1/storage/default", {
    fixture: "/privacy-requests/settings_configuration.json",
  }).as("getStorageDetails");

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

  cy.intercept("GET", "/api/v1/messaging/default/*", {
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
  cy.intercept("GET", "/api/v1/privacy-notice/*/available_translations", {
    fixture: "privacy-notices/available-translations.json",
  }).as("getAvailableTranslations");
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
    cy.fixture("plus_health.json").then((data) => {
      cy.intercept("GET", "/health", {
        statusCode: 200,
        body: { webserver: "healthy", version: "1.1.1", cache: "healthy" },
      }).as("getPlusHealth");
    });
    cy.intercept("GET", "/api/v1/plus/health", {
      statusCode: 400,
      body: {},
    }).as("getPlusHealth");
    cy.intercept("GET", "/api/v1/plus/*", {
      statusCode: 404,
      body: {},
    }).as("getNoPlusAvailable");
  }
};

export const stubHomePage = () => {
  cy.intercept("GET", "/api/v1/privacy-request*", {
    statusCode: 200,
    body: { items: [], total: 0, page: 1, size: 25 },
  }).as("getHomePagePrivacyRequests");
};

export const stubPrivacyRequests = (
  statusOverride?: PrivacyRequestStatus,
  policyOverride?: any,
) => {
  cy.fixture("privacy-requests/list.json").then(
    (privacyRequests: PrivacyRequestResponse) => {
      if (statusOverride) {
        privacyRequests.items[0].status = statusOverride;
      }
      if (policyOverride) {
        privacyRequests.items[0].policy = policyOverride;
      }
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
      cy.intercept(
        {
          method: "GET",
          pathname: "/api/v1/privacy-request",
          query: {
            include_identities: "true",
            page: "*",
            size: "*",
          },
        },
        { fixture: "privacy-requests/list.json" },
      ).as("getPrivacyRequests");
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

  cy.intercept(
    {
      method: "POST",
      pathname: "/api/v1/privacy-request/*/soft-delete",
    },
    { body: null },
  ).as("softDeletePrivacyRequest");

  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/privacy-request/notification",
    },
    { body: null },
  ).as("privacyRequestNotification");
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
  cy.intercept("GET", "/api/v1/plus/locations*", {
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
  cy.intercept("POST", "/api/v1/plus/dictionary/system-vendors", {
    body: {
      systems: [
        {
          id: "123",
          name: "Test System",
          fides_key: "test-system",
        },
      ],
    },
  }).as("postSystemVendors");
};

export const stubTranslationConfig = (enabled: boolean) => {
  cy.intercept("GET", "/api/v1/languages", {
    fixture: "languages.json",
  }).as("getLanguages");
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
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/**/confirm*", {
    response: 200,
  }).as("confirmResource");
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/mute*", {
    response: 200,
  }).as("ignoreResource");
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/promote*", {
    response: 200,
  }).as("promoteResource");
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/un-mute*", {
    response: 200,
  }).as("unmuteResource");
};

export const stubOpenIdProviders = () => {
  cy.intercept("GET", "/api/v1/plus/openid-provider/simple", {
    fixture: "openid-provider/openid-provider-simple.json",
  }).as("getOpenIdProvidersSimple");
  cy.intercept("GET", "/api/v1/plus/openid-provider", {
    fixture: "openid-provider/openid-provider.json",
  }).as("getOpenIdProviders");
};

export const stubSystemIntegrations = () => {
  cy.intercept("GET", "/api/v1/connection_type*", {
    fixture: "connectors/connection_types.json",
  }).as("getConnectionTypes");
  cy.intercept("GET", "/api/v1/connection_type/*/secret", {
    fixture: "connectors/postgres_secret.json",
  }).as("getPostgresConnectorSecret");
  cy.intercept("GET", "/api/v1/connection/datasetconfig?size=1000", {
    fixture: "connectors/datasetconfig.json",
  }).as("getConnectionDatasetConfig");
  cy.intercept("GET", "/api/v1/connection/*/datasetconfig?size=1000", {
    fixture: "connectors/datasetconfig.json",
  }).as("getConnectionDatasetConfig");
  cy.intercept("GET", "/api/v1/plus/dictionary/system?size=2000", {
    fixture: "dictionary-entries.json",
  }).as("getDict");
  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/connection",
      query: {
        page: "*",
        size: "*",
        orphaned_from_system: "true",
      },
    },
    {
      fixture: "connectors/bigquery_connection_list.json",
    },
  ).as("getConnections");
};

export const stubDisabledIntegrationSystemCrud = () => {
  cy.intercept("GET", "/api/v1/system/disabled_postgres_system", {
    fixture: "systems/system_disabled_integration.json",
  }).as("getDisabledSystemIntegration");

  cy.intercept("PATCH", "/api/v1/system/disabled_postgres_system/connection", {
    statusCode: 200,
    body: {},
  }).as("patchConnection");

  cy.intercept("PUT", "/api/v1/connection/asdasd_postgres/datasetconfig", {
    statusCode: 200,
    body: {},
  }).as("putDatasetConfig");

  cy.intercept(
    "PATCH",
    "/api/v1/system/disabled_postgres_system/connection/secrets*",
    {
      statusCode: 200,
      body: {},
    },
  ).as("patchConnectionSecret");
};

export const stubUserManagement = () => {
  cy.intercept("/api/v1/user?*", {
    fixture: "user-management/users.json",
  }).as("getAllUsers");
  cy.intercept("/api/v1/user/*", { fixture: "user-management/user.json" }).as(
    "getUser",
  );
  cy.intercept("/api/v1/user/*/permission", {
    fixture: "user-management/permissions.json",
  }).as("getPermissions");
  cy.intercept("/api/v1/user/*/system-manager", {
    fixture: "systems/systems.json",
  });
};

export const stubProperties = () => {
  cy.intercept("GET", "/api/v1/plus/properties*", {
    fixture: "properties/properties.json",
  }).as("getProperties");
};

export const stubExperienceConfig = () => {
  cy.intercept("GET", "/api/v1/experience-config*", {
    fixture: "privacy-experiences/list.json",
  }).as("getExperiences");
  cy.intercept("GET", "/api/v1/experience-config/pri*", {
    fixture: "privacy-experiences/experienceConfig.json",
  }).as("getExperienceDetail");
  cy.intercept("GET", "/api/v1/experience-config/*/available_translations", {
    fixture: "privacy-notices/available-translations.json",
  }).as("getAvailableTranslations");
  cy.intercept("GET", "/api/v1/experience-config/available_translations", {
    fixture: "privacy-notices/available-translations.json",
  }).as("getAvailableTranslations");
  cy.intercept("POST", "/api/v1/experience-config", {
    fixture: "privacy-experiences/experienceConfig.json",
  }).as("postExperience");
  cy.intercept("GET", "/api/v1/plus/tcf/configurations*", {
    fixture: "tcf/configurations.json",
  }).as("getTcfConfigs");
  stubPlus(true);
};

export const stubFidesCloud = () => {
  cy.intercept("GET", "/api/v1/plus/fides-cloud", {
    privacy_center_url: null,
    domain_verification_records: [],
  }).as("getFidesCloud");
};

export const stubWebsiteMonitor = () => {
  cy.intercept("GET", "/api/v1/config*", {
    body: {
      detection_discovery: {
        website_monitor_enabled: true,
      },
    },
  }).as("getTranslationConfig");
  cy.intercept("GET", "/api/v1/plus/discovery-monitor/aggregate-results*", {
    fixture: "detection-discovery/activity-center/aggregate-results",
  }).as("getMonitorResults");
  cy.intercept(
    "GET",
    "/api/v1/plus/discovery-monitor/system-aggregate-results*",
    {
      fixture: "detection-discovery/activity-center/system-aggregate-results",
    },
  ).as("getSystemAggregateResults");
  cy.intercept("GET", "/api/v1/plus/discovery-monitor/*/results*", {
    fixture: "detection-discovery/activity-center/system-asset-results",
  }).as("getSystemAssetResults");
  cy.intercept(
    "GET",
    "/api/v1/plus/discovery-monitor/*/results?*resolved_system_id=%5Bundefined%5D*",
    {
      fixture: "detection-discovery/activity-center/system-asset-uncategorized",
    },
  ).as("getSystemAssetsUncategorized");
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/mute*", {
    response: 200,
  }).as("ignoreAssets");
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/promote*", {
    response: 200,
  }).as("addAssets");
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/*/mute*", {
    response: 200,
  }).as("ignoreMonitorResultSystem");
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/*/promote*", {
    response: 200,
  }).as("addMonitorResultSystem");
  cy.intercept("PATCH", "/api/v1/plus/discovery-monitor/*/results", {
    response: 200,
  }).as("patchAssets");
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/un-mute*", {
    response: 200,
  }).as("restoreAssets");
  cy.intercept(
    "GET",
    "/api/v1/plus/discovery-monitor/staged_resource/*/consent*",
    {
      fixture: "detection-discovery/activity-center/consent-breakdown",
    },
  ).as("getConsentBreakdown");
  cy.intercept("GET", "/api/v1/plus/filters/website_monitor_resources*", {
    response: 200,
  }).as("getWebsiteMonitorResourcesFilters");
};

export const stubSystemAssets = () => {
  cy.intercept("GET", "/api/v1/plus/system-assets/*", {
    fixture: "systems/system_assets",
  }).as("getSystemAssets");
  cy.intercept("POST", "/api/v1/plus/system-assets/*/assets", {
    response: 200,
  }).as("addSystemAsset");
  cy.intercept("PUT", "/api/v1/plus/system-assets/*/assets*", {
    response: 200,
  }).as("updateSystemAssets");
  cy.intercept("DELETE", "/api/v1/plus/system-assets/*/assets*", {
    response: 200,
  }).as("deleteSystemAssets");
};

export const stubDataCatalog = () => {
  cy.intercept("GET", "/api/v1/plus/data-catalog/system*", {
    fixture: "data-catalog/catalog-systems",
  }).as("getCatalogSystems");
  cy.intercept("GET", "/api/v1/plus/data-catalog/project*", {
    fixture: "data-catalog/catalog-projects",
  }).as("getCatalogProjects");
  cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
    fixture: "data-catalog/catalog-tables",
  }).as("getCatalogTables");
  cy.intercept("POST", "/api/v1/plus/discovery-monitor/databases*", {
    items: ["test_project"],
    page: 1,
    size: 1,
    total: 1,
    pages: 1,
  }).as("getAvailableDatabases");
};

export const stubTCFConfig = () => {
  cy.intercept("/api/v1/config?api_set=false", {
    body: { consent: { override_vendor_purposes: true } },
  });
  cy.intercept("/api/v1/config?api_set=true", {
    body: { consent: { override_vendor_purposes: true } },
  });
  cy.intercept("PATCH", "/api/v1/config", { body: {} }).as("patchConfig");
  cy.intercept("GET", "/api/v1/plus/tcf/configurations*", {
    fixture: "tcf/configurations.json",
  }).as("getTcfConfigs");
  cy.intercept("GET", "/api/v1/purposes", {
    fixture: "tcf/purposes.json",
  }).as("getTcfPurposes");
  cy.intercept(
    "GET",
    "/api/v1/plus/tcf/configurations/*/publisher_restrictions?purpose_id=*",
    {
      fixture: "tcf/publisher-restrictions.json",
    },
  ).as("getTcfRestrictions");
  cy.intercept(
    "DELETE",
    "/api/v1/plus/tcf/configurations/*/publisher_restrictions/*",
    {
      body: {},
    },
  ).as("deleteRestriction");
  cy.fixture("tcf/configurations.json").then((data) => {
    cy.intercept("GET", "/api/v1/plus/tcf/configurations/*", {
      body: data.items[0],
    }).as("getTCFConfig");
  });
  cy.intercept("POST", "/api/v1/plus/tcf/configurations", {
    body: { id: "new-config-id" },
  }).as("createConfig");
  cy.intercept(
    "POST",
    "/api/v1/plus/tcf/configurations/*/publisher_restrictions",
    {
      body: {},
    },
  ).as("createRestriction");
};

export const stubConnectionTypes = () => {
  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/connection_type",
      query: {
        page: "*",
        size: "*",
      },
    },
    {
      fixture: "connectors/connection_types.json",
    },
  ).as("getConnectionTypes");

  cy.intercept("GET", "/api/v1/connection_type/*/secret", {
    fixture: "connectors/bigquery_secret.json",
  }).as("getSecretsSchema");
};

interface IntegrationManagementOptions {
  connectionListFixture?: string;
  connectionFixture?: string;
  secretSchemaFixture?: string;
}

export const stubIntegrationManagement = (
  options: IntegrationManagementOptions = {},
) => {
  const {
    connectionListFixture = "connectors/bigquery_connection_list.json",
    connectionFixture = "connectors/bigquery_connection.json",
    secretSchemaFixture = "connectors/bigquery_secret.json",
  } = options;

  // Use customized connection_type with specified secret schema fixture
  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/connection_type",
      query: {
        page: "*",
        size: "*",
      },
    },
    {
      fixture: "connectors/connection_types.json",
    },
  ).as("getConnectionTypes");

  cy.intercept("GET", "/api/v1/connection_type/*/secret", {
    fixture: secretSchemaFixture,
  }).as("getSecretsSchema");

  cy.intercept("GET", "/api/v1/connection/*/test", {
    statusCode: 200,
    body: {
      test_status: "succeeded",
    },
  }).as("testConnection");

  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/connection",
      query: {
        connection_type: "*",
      },
    },
    {
      fixture: connectionListFixture,
    },
  ).as("getConnections");

  cy.intercept("GET", "/api/v1/connection/*", {
    fixture: connectionFixture,
  }).as("getConnection");

  cy.intercept("GET", "/api/v1/connection", { body: undefined }).as(
    "unknownConnection",
  );

  cy.intercept("GET", "/api/v1/system", {
    fixture: "systems/systems.json",
  }).as("getSystems");
};

export const stubManualTaskConfig = () => {
  // Mock manual task related endpoints
  cy.intercept("GET", "/api/v1/plus/connection/*/manual-fields*", {
    fixture: "integration-management/manual-tasks/manual-fields.json",
  }).as("getManualFields");

  cy.intercept("POST", "/api/v1/plus/connection/*/manual-field", {
    body: {},
  }).as("createManualField");

  cy.intercept("PUT", "/api/v1/plus/connection/*/manual-field/*", {
    body: {},
  }).as("updateManualField");

  cy.intercept("DELETE", "/api/v1/plus/connection/*/manual-field/*", {
    statusCode: 204,
  }).as("deleteManualField");

  cy.intercept("GET", "/api/v1/connection/demo_manual_task_integration", {
    fixture: "integration-management/manual-tasks/manual-task-connection.json",
  }).as("getConnection");

  // Mock user assignment endpoints
  cy.intercept("GET", "/api/v1/plus/connection/*/manual-task", {
    fixture: "integration-management/manual-tasks/task-config.json",
  }).as("getManualTask");

  cy.intercept("PUT", "/api/v1/plus/connection/*/manual-task/assign-users", {
    body: {},
  }).as("assignUsersToManualTask");

  // Mock external user creation
  cy.intercept("POST", "/api/v1/plus/external-user", {
    body: {},
  }).as("createExternalUser");

  // Mock dependency conditions endpoints
  cy.intercept(
    "PUT",
    "/api/v1/plus/connection/*/manual-task/dependency-conditions",
    {
      body: {},
    },
  ).as("updateDependencyConditions");

  // Mock dataset endpoints for DatasetReferencePicker
  cy.intercept(
    "GET",
    "/api/v1/dataset?minimal=true&exclude_saas_datasets=true",
    {
      fixture: "datasets.json",
    },
  ).as("getFilteredDatasets");

  cy.intercept("GET", "/api/v1/dataset/*", {
    fixture: "dataset.json",
  }).as("getDatasetByKey");
};

export const stubSharedMonitorConfig = () => {
  cy.intercept("GET", "/api/v1/plus/shared-monitor-config*", {
    fixture: "detection-discovery/monitors/shared_config_response.json",
  }).as("getSharedMonitorConfig");
  cy.intercept("POST", "/api/v1/plus/shared-monitor-config", {
    response: 200,
  }).as("createSharedMonitorConfig");
};

export const stubManualTasks = () => {
  // Intercept this call that is made to get the full list of filters available
  cy.intercept("GET", "/api/v1/plus/manual-fields?page=1&size=1", {
    fixture: "manual-tasks/manual-tasks-response.json",
  }).as("getManualTasksFullFilters");

  // Intercept the manual tasks API endpoints
  cy.intercept("GET", "/api/v1/plus/manual-fields?page=1&size=25*", {
    fixture: "manual-tasks/manual-tasks-response.json",
  }).as("getManualTasks");

  cy.intercept("POST", "/api/v1/privacy-request/*/manual-field/*/complete", {
    body: {
      manual_field_id: "task_001",
      status: "completed",
    },
  }).as("completeTask");

  cy.intercept("POST", "/api/v1/privacy-request/*/manual-field/*/skip", {
    body: {
      manual_field_id: "task_001",
      status: "skipped",
    },
  }).as("skipTask");

  cy.intercept("GET", "/api/v1/plus/manual-fields/*", {
    fixture: "manual-tasks/manual-task-detail.json",
  }).as("getTaskById");
};

export const stubFeatureFlags = () => {
  // Intercept the manual tasks API endpoints
  cy.intercept("GET", "/api/v1/config*", {
    fixture: "/privacy-requests/settings_configuration.json",
  }).as("createConfigurationSettings");
};

export const stubLogout = () => {
  cy.intercept("POST", "/api/v1/logout", {
    statusCode: 204,
  }).as("logoutRequest");
};

export const stubPlusAuth = () => {
  cy.intercept("GET", "/api/v1/plus/authentication-methods", {
    statusCode: 200,
    body: {},
  }).as("logoutRequest");
};
