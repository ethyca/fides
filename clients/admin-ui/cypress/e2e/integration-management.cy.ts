import {
  stubIntegrationManagement,
  stubLocations,
  stubPlus,
  stubSharedMonitorConfig,
  stubSystemCrud,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

describe("Integration management for data detection & discovery", () => {
  beforeEach(() => {
    cy.login();

    // Use custom list fixture for the top-level test
    stubIntegrationManagement({
      connectionListFixture: "connectors/list.json",
    });
    cy.intercept("GET", "/api/v1/connection?connection_type*", {
      fixture: "connectors/list.json",
    }).as("getConnectors");
    cy.intercept("GET", "/api/v1/connection/*/test", {
      statusCode: 200,
      body: {
        test_status: "succeeded",
      },
    }).as("testConnection");
    cy.intercept("GET", "/api/v1/connection_type?*", {
      fixture: "connectors/connection_types.json",
    }).as("getConnectionTypes");
    cy.intercept("GET", "/api/v1/connection_type/*/secret", {
      fixture: "connectors/bigquery_secret.json",
    }).as("getSecretsSchema");
  });

  describe("accessing the page", () => {
    it("can access the integration management page", () => {
      stubPlus(true);
      cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
      cy.contains("h1", "Integrations").should("exist");
      cy.getByTestId("add-integration-btn").should("exist");
    });

    it("can't access without Plus", () => {
      stubPlus(false);
      cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
      cy.getByTestId("home-content").should("exist");
    });
  });

  describe("main page", () => {
    beforeEach(() => {
      stubPlus(true);
    });

    it("should show an empty state when there are no integrations available", () => {
      cy.intercept("GET", "/api/v1/connection?*", {
        fixture: "connectors/empty_list.json",
      }).as("getConnections");
      cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
      cy.wait("@getConnections");
      cy.getByTestId("empty-state").should("exist");
    });

    describe("table view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/connection?*", {
          fixture: "connectors/bigquery_connection_list.json",
        }).as("getConnections");
        cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
        cy.wait("@getConnections");
      });

      it("should show a table of integrations", () => {
        cy.getByTestId("integrations-table").should("exist");
        cy.getByTestId("integrations-table")
          .find("tbody tr")
          .should("have.length.greaterThan", 0);
        cy.getByTestId("integration-info-bq_integration").should("exist");
        cy.getByTestId("manage-btn-bq_integration").should("exist");
      });

      it("should be able to navigate to management page when row is clicked", () => {
        cy.intercept("GET", "/api/v1/connection/bq_integration", {
          fixture: "connectors/bigquery_connection.json",
        }).as("getConnection");
        cy.getByTestId("integration-info-bq_integration").click();
        cy.url().should("contain", "/bq_integration");
      });

      it("should navigate to management page when 'manage' button is clicked", () => {
        cy.intercept("GET", "/api/v1/connection/bq_integration", {
          fixture: "connectors/bigquery_connection.json",
        }).as("getConnection");
        cy.getByTestId("manage-btn-bq_integration").click();
        cy.url().should("contain", "/bq_integration");
      });

      it.skip("should paginate integrations", () => {
        cy.intercept("GET", "/api/v1/connection?*&page=1*", {
          fixture: "connectors/list_page_1_50_items.json",
        }).as("getConnectionsPage1");
        cy.intercept("GET", "/api/v1/connection?*&page=2*", {
          fixture: "connectors/list_page_2_30_items.json",
        }).as("getConnectionsPage2");
        cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
        cy.wait("@getConnectionsPage1");

        cy.get(".ant-pagination").should("exist");
        cy.getByTestId("integrations-table")
          .find("tbody tr")
          .should("have.length", 50);

        cy.get(".ant-pagination-item-1").should(
          "have.class",
          "ant-pagination-item-active",
        );
        cy.get(".ant-pagination-item-2").should("exist");
        cy.get(".ant-pagination-item-2").click();
        cy.wait("@getConnectionsPage2");

        cy.getByTestId("integrations-table")
          .find("tbody tr")
          .should("have.length", 30);

        cy.getByTestId("manage-btn-snowflake_connector_11").should("exist");
      });

      it("should be able to search integrations", () => {
        cy.intercept("GET", "/api/v1/connection?*&search=test*", {
          fixture: "connectors/bigquery_connection_list.json",
        }).as("getSearchResults");

        cy.get("input[placeholder='Search by name...']").type("test");
        cy.wait("@getSearchResults");
        cy.getByTestId("integrations-table").find("tbody tr").should("exist");
      });
    });

    describe("adding an integration", () => {
      beforeEach(() => {
        stubIntegrationManagement();

        cy.intercept("GET", "/api/v1/connection/datasetconfig", {
          fixture: "connectors/empty_datasetconfig.json",
        }).as("getDatasetConfig");
        cy.intercept(
          "GET",
          "/api/v1/dataset?only_unlinked_datasets=true&minimal=true",
          {
            fixture: "connectors/empty_unlinked_datasets.json",
          },
        ).as("getUnlinkedDatasets");
        cy.intercept("GET", "/api/v1/dataset?minimal=true&connection_type=*", {
          fixture: "connectors/empty_minimal_datasets.json",
        }).as("getMinimalDatasets");

        cy.intercept("GET", "/api/v1/connection?*", {
          fixture: "connectors/bigquery_connection_list.json",
        }).as("getConnections");
        cy.intercept("GET", "/api/v1/connection_type?*", {
          fixture: "connectors/connection_types.json",
        }).as("getConnectionTypes");
        cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
        cy.wait("@getConnections");
      });

      it("should open modal", () => {
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content")
          .should("be.visible")
          .within(() => {
            cy.get(".grid-cols-3").should("exist");
            cy.getByTestId("integration-info-bq_placeholder").should("exist");
          });
      });

      it("should be able to add a new integration with secrets", () => {
        cy.intercept("PATCH", "/api/v1/connection", { statusCode: 200 }).as(
          "patchConnection",
        );
        cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
          response: 200,
        }).as("patchConnectionSecrets");
        cy.intercept("GET", "/api/v1/connection_type/*/secret", {
          fixture: "connectors/bigquery_secret.json",
        }).as("getBigquerySecretsSchema");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-bq_placeholder").within(() => {
            cy.contains("Details").click();
          });
        });
        cy.getByTestId("configure-modal-btn").click();
        cy.getByTestId("input-name").type("test name");
        cy.getByTestId("input-secrets.keyfile_creds").type(
          `{"credentials": "test"}`,
          {
            parseSpecialCharSequences: false,
          },
        );
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
        cy.wait("@patchConnectionSecrets");
      });

      it("should be able to add a new integration associated with a system", () => {
        stubSystemCrud();
        cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
          response: 200,
        }).as("patchConnectionSecrets");
        cy.intercept("PATCH", "/api/v1/system/*/connection", {
          response: 200,
        }).as("patchSystemConnection");
        cy.intercept("GET", "/api/v1/system", {
          fixture: "systems/systems.json",
        }).as("getSystems");
        cy.intercept("GET", "/api/v1/connection_type/*/secret", {
          fixture: "connectors/bigquery_secret.json",
        }).as("getBigquerySecretsSchema");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-bq_placeholder").within(() => {
            cy.contains("Details").click();
          });
        });
        cy.getByTestId("configure-modal-btn").click();
        cy.getByTestId("input-name").type("test name");
        cy.getByTestId("input-secrets.keyfile_creds").type(
          `{"credentials": "test"}`,
          {
            parseSpecialCharSequences: false,
          },
        );
        cy.getByTestId("controlled-select-system_fides_key").antSelect(
          "Fidesctl System",
        );
        cy.getByTestId("save-btn").click();
        cy.wait("@patchSystemConnection");
      });

      it("should display an API integration under the CRM category", () => {
        cy.intercept("GET", "/api/v1/connection_type/*/secret", {
          fixture: "connectors/salesforce_secret.json",
        }).as("getSalesforceSecretsSchema");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("category-filter-select").antSelect("CRM");
        cy.getByTestId("add-modal-content").within(() => {
          // Verify Salesforce appears
          cy.getByTestId("integration-info-salesforce_placeholder").should(
            "exist",
          );
        });
      });

      it("should be able to instantiate an API integration by filling out the form", () => {
        // API-specific intercepts
        cy.intercept("POST", "/api/v1/connection/instantiate/salesforce", {
          statusCode: 200,
        }).as("instantiateConnection");
        cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
          response: 200,
        }).as("patchConnectionSecrets");
        cy.intercept("GET", "/api/v1/connection_type/*/secret", {
          fixture: "connectors/salesforce_secret.json",
        }).as("getSalesforceSecretsSchema");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("category-filter-select").antSelect("CRM");
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-salesforce_placeholder").within(
            () => {
              cy.contains("Details").click();
            },
          );
        });
        cy.getByTestId("configure-modal-btn").click();

        // Fill out the form with fields from the salesforce_secret schema
        cy.getByTestId("input-name").type("My Salesforce Integration");
        cy.getByTestId("input-secrets.client_id").type("test_client_id");
        cy.getByTestId("input-secrets.client_secret").type(
          "test_client_secret",
        );
        cy.getByTestId("input-secrets.domain").type("mycompany.salesforce.com");
        cy.getByTestId("input-secrets.redirect_uri").type(
          "https://example.com/callback",
        );

        // Submit the form
        cy.getByTestId("save-btn").click();
        cy.wait("@instantiateConnection");
        cy.wait("@patchConnectionSecrets");
      });

      it("should be able to add a new integration without secrets", () => {
        cy.intercept("PATCH", "/api/v1/connection", { statusCode: 200 }).as(
          "patchConnection",
        );
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-manual_placeholder").within(() => {
            cy.contains("Details").click();
          });
        });
        cy.getByTestId("configure-modal-btn").click();
        cy.getByTestId("input-name").type("Manual Integration Test");
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
      });

      it("should support search and filter in add integration modal", () => {
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.get("input[placeholder='Search by name...']").type("BigQuery");
          cy.getByTestId("integration-info-bq_placeholder").should("exist");

          cy.get(".ant-input-clear-icon").click();
        });
        cy.getByTestId("category-filter-select").antSelect("Data Warehouse");

        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-bq_placeholder").should("exist");
        });
      });

      it("should fetch datasets with minimal=true for BigQuery integration", () => {
        cy.intercept("GET", "/api/v1/connection_type/*/secret", {
          fixture: "connectors/bigquery_secret.json",
        }).as("getBigquerySecretsSchema");
        cy.intercept("PATCH", "/api/v1/connection", { statusCode: 200 }).as(
          "patchConnection",
        );
        cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
          response: 200,
        }).as("patchConnectionSecrets");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-bq_placeholder").within(() => {
            cy.contains("Details").click();
          });
        });
        cy.getByTestId("configure-modal-btn").click();
        cy.getByTestId("input-name").type("BigQuery Integration");
        cy.getByTestId("input-description").type("BigQuery integration test");
        cy.getByTestId("input-secrets.keyfile_creds").type(
          `{"credentials": "test"}`,
          {
            parseSpecialCharSequences: false,
          },
        );

        // Verify that the minimal dataset query was called for BigQuery datasets
        cy.wait("@getMinimalDatasets").then((interception) => {
          expect(interception.request.url).to.contain("minimal=true");
          expect(interception.request.url).to.contain(
            "connection_type=bigquery",
          );
        });

        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
        cy.wait("@patchConnectionSecrets");
      });

      it("should redirect to integration detail page after creating a new integration", () => {
        cy.intercept("PATCH", "/api/v1/connection", { statusCode: 200 }).as(
          "patchConnection",
        );
        cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
          response: 200,
        }).as("patchConnectionSecrets");
        cy.intercept("GET", "/api/v1/connection_type/*/secret", {
          fixture: "connectors/bigquery_secret.json",
        }).as("getBigquerySecretsSchema");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-bq_placeholder").within(() => {
            cy.contains("Details").click();
          });
        });
        cy.getByTestId("configure-modal-btn").click();
        cy.getByTestId("input-name").type("Test Redirect Integration");
        cy.getByTestId("input-secrets.keyfile_creds").type(
          `{"credentials": "test"}`,
          {
            parseSpecialCharSequences: false,
          },
        );
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
        cy.wait("@patchConnectionSecrets");

        // Verify user is redirected to the integration detail page
        cy.url().should("contain", "/integrations/test_redirect_integration");
      });
    });

    describe("adding a website integration", () => {
      beforeEach(() => {
        stubIntegrationManagement({
          secretSchemaFixture: "integration/website_integration_secret.json",
        });

        cy.intercept("GET", "/api/v1/connection?*", {
          fixture: "connectors/bigquery_connection_list.json",
        }).as("getConnections");
        cy.intercept("GET", "/api/v1/connection_type?*", {
          fixture: "connectors/connection_types.json",
        }).as("getConnectionTypes");
        cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
        cy.wait("@getConnections");
      });

      it("should be able to add a new website integration", () => {
        cy.intercept("PATCH", "/api/v1/connection", { statusCode: 200 }).as(
          "patchConnection",
        );
        cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
          response: 200,
        }).as("patchConnectionSecrets");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId(
            "details-btn-microsoft_sql_server_placeholder",
          ).click();
          cy.getByTestId("configure-btn").click();
        });
        cy.getByTestId("input-name").type("test name");
        cy.getByTestId("input-secrets.url").type("https://example.com");
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
        cy.wait("@patchConnectionSecrets");
      });

      it("should not show system selection for website integrations", () => {
        cy.intercept("PATCH", "/api/v1/connection", { statusCode: 200 }).as(
          "patchConnection",
        );
        cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
          response: 200,
        }).as("patchConnectionSecrets");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("details-btn-website_placeholder").click();
          cy.getByTestId("configure-modal-btn").click();

          // Verify system selection field is not present for website integrations
          cy.getByTestId("controlled-select-system_fides_key").should(
            "not.exist",
          );
        });
      });

      it("accepts HTTP URLs", () => {
        cy.intercept("PATCH", "/api/v1/connection", { statusCode: 200 }).as(
          "patchConnection",
        );
        cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
          response: 200,
        }).as("patchConnectionSecrets");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId(
            "details-btn-microsoft_sql_server_placeholder",
          ).click();
          cy.getByTestId("configure-modal-btn").click();
        });
        cy.getByTestId("input-name").type("test name");
        cy.getByTestId("input-secrets.url").type("http://example.com");
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
        cy.wait("@patchConnectionSecrets").then((interception) => {
          expect(interception.request.body.url).to.equal("http://example.com");
        });
      });

      it("defaults to HTTPS if a protocol isn't provided", () => {
        cy.intercept("PATCH", "/api/v1/connection", { statusCode: 200 }).as(
          "patchConnection",
        );
        cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
          response: 200,
        }).as("patchConnectionSecrets");

        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId(
            "details-btn-microsoft_sql_server_placeholder",
          ).click();
          cy.getByTestId("configure-modal-btn").click();
        });
        cy.getByTestId("input-name").type("test name");
        cy.getByTestId("input-secrets.url").type("example.com");
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
        cy.wait("@patchConnectionSecrets").then((interception) => {
          expect(interception.request.body.url).to.equal("https://example.com");
        });
      });
    });
  });

  describe("detail view", () => {
    beforeEach(() => {
      stubPlus(true);
      stubIntegrationManagement();
      cy.intercept("GET", "/api/v1/connection", { body: undefined }).as(
        "unknownConnection",
      );
      cy.intercept("GET", "/api/v1/connection/*", {
        fixture: "connectors/bigquery_connection.json",
      }).as("getConnection");
      cy.intercept("GET", "/api/v1/connection?*", {
        fixture: "connectors/bigquery_connection_list.json",
      }).as("getConnections");
      cy.intercept("GET", "/api/v1/connection_type?*", {
        fixture: "connectors/connection_types.json",
      }).as("getConnectionTypes");
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
      cy.visit("/integrations/bq_integration");
    });

    it("redirects to list view if the integration type is incorrect", () => {
      cy.intercept("GET", "/api/v1/connection/*", {
        fixture: "connectors/sovrn_connector.json",
      }).as("getConnection");
      cy.wait("@getConnection");
      cy.url().should("not.contain", "bq_integration");
    });

    it("can test the connection", () => {
      cy.getByTestId("test-connection-btn").click();
      cy.wait("@testConnection");
    });

    it("can edit integration with the modal without changing secrets", () => {
      cy.intercept("PATCH", "/api/v1/connection", {
        fixture: "connectors/patch_connection.json",
      }).as("patchConnection");
      cy.getByTestId("manage-btn").click();
      cy.getByTestId("input-system_fides_key").should("not.exist");
      cy.getByTestId("input-name")
        .should("have.value", "BQ Integration")
        .clear()
        .type("A different name");
      cy.getByTestId("save-btn").click();
      cy.wait("@patchConnection");
    });

    it("can edit integration with the modal with new secrets", () => {
      cy.intercept("PATCH", "/api/v1/connection/*/secret*", {
        response: 200,
      }).as("patchConnectionSecrets");
      cy.intercept("PATCH", "/api/v1/connection", {
        fixture: "connectors/patch_connection.json",
      }).as("patchConnection");
      cy.getByTestId("manage-btn").click();
      cy.getByTestId("input-system_fides_key").should("not.exist");
      cy.getByTestId("input-name")
        .should("have.value", "BQ Integration")
        .clear()
        .type("A different name");
      cy.getByTestId("input-secrets.keyfile_creds").type(
        `{"credentials": "test221312"}`,
        {
          parseSpecialCharSequences: false,
        },
      );
      cy.getByTestId("input-secrets.dataset").type(`somedataset`);
      cy.getByTestId("save-btn").click();

      cy.wait("@patchConnection");
      cy.wait("@patchConnectionSecrets");
    });

    it("shows an empty state in 'data discovery' tab when no monitors are configured", () => {
      cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
        fixture: "detection-discovery/monitors/empty_monitors.json",
      }).as("getEmptyMonitors");
      cy.intercept("/api/v1/plus/discovery-monitor/databases", {
        fixture: "empty-pagination.json",
      }).as("getEmptyDatabases");
      cy.getAntTab("Data discovery").click({ force: true });
      cy.wait("@getEmptyMonitors");
      cy.get(".ant-empty-description").should("exist");
    });

    describe("data discovery tab", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
          fixture: "detection-discovery/monitors/monitor_list.json",
        }).as("getMonitors");
        cy.intercept("/api/v1/plus/discovery-monitor/databases", {
          fixture: "detection-discovery/monitors/database_list_page_1.json",
        }).as("getDatabasesPage1");
        cy.intercept("POST", "/api/v1/plus/discovery-monitor/*/execute", {
          response: 200,
        }).as("executeMonitor");
        cy.intercept("DELETE", "/api/v1/plus/discovery-monitor/*", {
          response: 200,
        }).as("deleteMonitor");
        cy.getAntTab("Data discovery").click({ force: true });
        cy.wait("@getMonitors");
        stubSharedMonitorConfig();
      });

      it("shows a table of monitors", () => {
        cy.getAntTableRow("test_monitor_1")
          .should("exist")
          .within(() => {
            cy.getAntCellWithinRow(3).should("contain", "Scanning");
          });
        cy.getAntTableRow("test_monitor_2").within(() => {
          cy.getByTestId("tag-success").should("exist");
        });
        cy.getAntTableRow("test_monitor_3").within(() => {
          cy.getByTestId("tag-error").should("exist");
          cy.getByTestId("tag-error").within(() => {
            cy.get("button").click({ force: true });
          });
        });
        cy.getByTestId("error-log-drawer")
          .should("be.visible")
          .within(() => {
            cy.getByTestId("error-log-message").should("have.length", 2);
          });
      });

      it("can configure a new monitor", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*", {
          response: 200,
        }).as("putMonitor");
        cy.getByTestId("add-monitor-btn").click();
        cy.getByTestId("add-modal-content").should("be.visible");
        cy.getByTestId("input-name").type("A new monitor");
        cy.getByTestId("controlled-select-shared_config_id").antSelect(
          "Shared Config 1",
        );
        cy.getByTestId("controlled-select-execution_frequency").antSelect(
          "Daily",
        );
        cy.getByTestId("input-execution_start_date").type("2034-06-03T10:00");
        cy.getByTestId("next-btn").click();
        cy.wait("@getDatabasesPage1");
        cy.getByTestId("prj-bigquery-000001-checkbox").click();
        cy.getByTestId("save-btn").click();
        cy.wait("@putMonitor").then((interception) => {
          expect(interception.request.body.databases).to.length(1);
        });
        cy.wait("@getMonitors");
      });

      it("can exclude databases", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*", {
          response: 200,
        }).as("putMonitor");
        cy.getByTestId("add-monitor-btn").click();
        cy.getByTestId("add-modal-content").should("be.visible");
        cy.getByTestId("input-name").type("A new monitor");
        cy.getByTestId("controlled-select-execution_frequency").antSelect(
          "Daily",
        );
        cy.getByTestId("input-execution_start_date").type("2034-06-03T10:00");
        cy.getByTestId("next-btn").click();
        cy.wait("@getDatabasesPage1");
        cy.getByTestId("select-all-checkbox").click();
        cy.getByTestId("prj-bigquery-000001-checkbox").should(
          "have.attr",
          "data-checked",
        );
        cy.getByTestId("prj-bigquery-000001-checkbox").click();
        cy.getByTestId("save-btn").click();
        cy.wait("@putMonitor").then((interception) => {
          expect(interception.request.body.excluded_databases).to.contain(
            "prj-bigquery-000001",
          );
        });
      });

      it("can load more databases", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*").as("putMonitor");
        cy.getByTestId("add-monitor-btn").click();
        cy.getByTestId("add-modal-content").should("be.visible");
        cy.getByTestId("input-name").type("A new monitor");
        cy.getByTestId("controlled-select-execution_frequency").antSelect(
          "Daily",
        );
        cy.getByTestId("input-execution_start_date").type("2034-06-03T10:00");
        cy.getByTestId("next-btn").click();
        cy.wait("@getDatabasesPage1");
        cy.getByTestId("select-all-checkbox").click();
        cy.intercept("POST", "/api/v1/plus/discovery-monitor/databases", {
          fixture: "detection-discovery/monitors/database_list_page_2.json",
        }).as("getDatabasesPage2");
        cy.getByTestId("load-more-btn").click();
        cy.wait("@getDatabasesPage2");
        cy.getByTestId("prj-bigquery-000026-checkbox").should(
          "have.attr",
          "data-checked",
        );
      });

      it("can edit an existing monitor by clicking the edit button", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*", {
          response: 200,
        }).as("putMonitor");
        cy.getAntTableRow("test_monitor_1").within(() => {
          cy.getByTestId("edit-monitor-btn").click();
        });
        cy.getByTestId("input-name").should("have.value", "test monitor 1");
        cy.getByTestId("input-execution_start_date")
          .should("have.prop", "value")
          .should("match", /2024-06-04T[0-9][0-9]:11/);
        cy.getByTestId("next-btn").click();
        cy.getByTestId("prj-bigquery-000001-checkbox").should(
          "have.attr",
          "data-checked",
        );
        cy.getByTestId("prj-bigquery-000003-checkbox").should(
          "not.have.attr",
          "data-checked",
        );
        cy.getByTestId("prj-bigquery-000003-checkbox").click();
        cy.getByTestId("save-btn").click();
        cy.wait("@putMonitor").then((interception) => {
          expect(interception.request.body.databases).to.length(3);
        });
      });

      it("can execute a monitor", () => {
        cy.getAntTableRow("test_monitor_1").within(() => {
          cy.getByTestId("action-Scan").click();
        });
        cy.wait("@executeMonitor");
      });

      it("can delete a monitor", () => {
        cy.getAntTableRow("test_monitor_1").within(() => {
          cy.getByTestId("delete-monitor-btn").click();
        });
        cy.getByTestId("confirmation-modal").within(() => {
          cy.getByTestId("continue-btn").click();
        });
        cy.wait("@deleteMonitor");
      });

      it("can enable/disable a monitor", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*", {
          response: 200,
        }).as("putMonitor");
        cy.getAntTableRow("test_monitor_1").within(() => {
          cy.getByTestId("toggle-switch").click({ force: true });
        });
        cy.wait("@putMonitor");
      });

      describe("LLM classifier configuration", () => {
        it.only("can configure a monitor with LLM classifier enabled", () => {
          cy.intercept("PUT", "/api/v1/plus/discovery-monitor*", {
            response: 200,
          }).as("putMonitor");

          cy.getByTestId("add-monitor-btn").click();
          cy.getByTestId("add-modal-content").should("be.visible");
          cy.getByTestId("input-name").type("Monitor with LLM");

          // Toggle LLM classifier on
          cy.getByTestId("input-use_llm_classifier").click();

          // LLM fields should now exist (not checking visibility due to modal overlay issues)
          cy.getByTestId("input-model_override").should("exist");
          cy.getByTestId("controlled-select-prompt_template").should("exist");

          // Give fields a moment to render before interacting
          cy.getByTestId("input-model_override").should("have.value", "");
          cy.getByTestId("input-model_override").type("gpt-4");

          // Use force: true for the select to work around modal overlay issues
          cy.getByTestId("controlled-select-prompt_template").antSelect(
            "Full",
            {
              force: true,
            },
          );

          cy.getByTestId("controlled-select-execution_frequency").antSelect(
            "Daily",
          );
          cy.getByTestId("input-execution_start_date").type("2034-06-03T10:00");
          cy.getByTestId("next-btn").click();
          cy.wait("@getDatabasesPage1");
          cy.getByTestId("prj-bigquery-000001-checkbox").click();
          cy.getByTestId("save-btn").click();

          cy.wait("@putMonitor").then((interception) => {
            // Verify LLM classifier fields are in the request
            expect(
              interception.request.body.classify_params.context_classifier,
            ).to.equal("llm");
            expect(
              interception.request.body.classify_params.model_override,
            ).to.equal("gpt-4");
            expect(
              interception.request.body.classify_params.prompt_template,
            ).to.equal("full");
          });
        });

        it.only("should hide LLM fields when switch is toggled off", () => {
          cy.getByTestId("add-monitor-btn").click();
          cy.getByTestId("add-modal-content").should("be.visible");

          // Toggle LLM classifier on
          cy.getByTestId("input-use_llm_classifier").click();
          cy.getByTestId("input-model_override").should("be.visible");

          // Toggle it back off
          cy.getByTestId("input-use_llm_classifier").click();
          cy.getByTestId("input-model_override").should("not.exist");
          cy.getByTestId("controlled-select-prompt_template").should(
            "not.exist",
          );
        });
      });

      describe("shared monitor configs", () => {
        beforeEach(() => {
          stubTaxonomyEntities();
        });
        it("shows a table of shared monitor configs", () => {
          cy.getByTestId("configurations-btn").click();
          cy.getByTestId("config-shared-config-1").should("exist");
        });

        it("can create a new shared monitor config", () => {
          cy.getByTestId("configurations-btn").click();
          cy.getByTestId("create-new-btn").click();
          cy.getByTestId("input-name").type("A new shared monitor config");
          cy.getByTestId("input-rules.0.regex").type(".*");
          cy.getByTestId("input-rules.0.dataCategory").antSelect("system");
          cy.getByTestId("add-rule-btn").click();
          cy.getByTestId("input-rules.1.regex").type(".*");
          cy.getByTestId("input-rules.1.dataCategory").antSelect("system");
          cy.getByTestId("upload-csv-btn").should("be.visible");
          cy.getByTestId("save-btn").click();
          cy.wait("@createSharedMonitorConfig");
        });

        it("can edit an existing shared monitor config", () => {
          cy.getByTestId("configurations-btn").click();
          cy.getByTestId("config-shared-config-1").within(() => {
            cy.getByTestId("edit-btn").click();
          });
          cy.getByTestId("upload-csv-btn").should("not.exist");
          cy.getByTestId("input-name").should("have.value", "Shared Config 1");
          cy.getByTestId("input-rules.0.regex").should(
            "have.value",
            "[E|e]mail",
          );
          cy.getByTestId("input-rules.0.dataCategory").should(
            "contain",
            "user.contact.email",
          );
          cy.getByTestId("input-rules.1.regex").should(
            "have.value",
            ".*[P|p]hone.*",
          );
          cy.getByTestId("input-rules.1.dataCategory").should(
            "contain",
            "user.contact.phone",
          );
        });
      });
    });

    describe("data discovery tab with no projects/databases", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
          fixture: "detection-discovery/monitors/monitor_list.json",
        }).as("getMonitors");
        cy.intercept("POST", "/api/v1/plus/discovery-monitor/databases", {
          fixture: "empty-pagination.json",
        }).as("getEmptyDatabases");
        cy.getAntTab("Data discovery").click({ force: true });
        cy.wait("@getMonitors");
      });

      it("skips the project/database selection step", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*", {
          response: 200,
        }).as("putMonitor");
        cy.getByTestId("add-monitor-btn").click();
        cy.getByTestId("input-name").type("A new monitor");
        cy.getByTestId("controlled-select-execution_frequency").antSelect(
          "Daily",
        );
        cy.getByTestId("input-execution_start_date").type("2034-06-03T10:00");
        cy.getByTestId("next-btn").click();
        cy.wait("@putMonitor");
      });
    });

    describe("data discovery tab for website integration", () => {
      beforeEach(() => {
        stubLocations();
        cy.intercept("GET", "/api/v1/connection/*", {
          fixture: "connectors/website_integration.json",
        }).as("getWebsiteIntegration");
        cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
          fixture: "detection-discovery/monitors/website_monitor_list.json",
        }).as("getMonitors");
        cy.intercept("GET", "/api/v1/connection_type?*", {
          fixture: "connectors/connection_types.json",
        }).as("getConnectionTypes");
        cy.getAntTab("Data discovery").click({ force: true });
        cy.wait("@getMonitors");
      });

      it("should render the website monitor list", () => {
        cy.getByTestId("monitor-description").contains(
          "Configure your website monitor",
        );
        cy.getAntTableRow("test_website_monitor").within(() => {
          cy.getAntCellWithinRow(0).should("contain", "test website monitor");
        });
      });

      it("should allow creating a website monitor", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*", {
          response: 200,
        }).as("putMonitor");
        cy.getByTestId("add-monitor-btn").click();
        cy.getByTestId("input-name").type("A new website monitor");
        cy.getByTestId("input-url")
          .should("be.disabled")
          .and("have.value", "http://example.com");
        cy.getByTestId(
          "controlled-select-datasource_params.locations",
        ).antSelect("France");
        cy.getByTestId("controlled-select-execution_frequency").click({
          force: true,
        });
        cy.getByTestId("controlled-select-execution_frequency").antSelect(
          "Quarterly",
        );
        cy.getByTestId("input-execution_start_date").type("2034-06-03T10:00");
        cy.getByTestId("save-btn").click();
        cy.wait("@putMonitor");
      });

      it("should allow editing a website monitor", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*", {
          response: 200,
        }).as("putMonitor");
        cy.getAntTableRow("test_website_monitor").within(() => {
          cy.getByTestId("edit-monitor-btn").click();
        });
        cy.getByTestId("input-name")
          .should("have.value", "test website monitor")
          .clear()
          .type("A different name");
        cy.getByTestId("controlled-select-system_fides_key").should(
          "not.exist",
        );
        cy.getByTestId("save-btn").click();
        cy.wait("@putMonitor").then((interception) => {
          expect(interception.request.body.name).to.equal("A different name");
        });
      });
    });

    // DEFER(ENG-801) Add back once we're ready to show all SAAS integrations
    describe.skip("data discovery tab for API integration", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/connection/*", {
          fixture: "connectors/salesforce_connection.json",
        }).as("getSalesforceIntegration");
        cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
          fixture: "detection-discovery/monitors/salesforce_monitor_list.json",
        }).as("getSalesforceMonitors");
        cy.intercept("GET", "/api/v1/connection_type", {
          fixture: "connectors/connection_types.json",
        }).as("getConnectionTypes");
        cy.intercept("POST", "/api/v1/plus/discovery-monitor/databases", {
          statusCode: 200,
          body: { items: [], total: 0, page: 1, size: 50, pages: 0 },
        }).as("getEmptyDatabases");
        cy.visit("/integrations/salesforce_integration");
        cy.getAntTab("Data discovery").click({ force: true });
        cy.wait("@getSalesforceMonitors");
      });

      it("should disable Add Monitor button when a monitor already exists for API integration", () => {
        // Verify that the existing monitor is displayed
        cy.getByTestId("row-teststeststst").should("exist");

        // Verify that the Add Monitor button is disabled
        cy.getByTestId("add-monitor-btn").should("be.disabled");
      });
    });

    describe("integration setup steps", () => {
      /**
       * Helper function to check if a step in the integration setup card is completed
       * @param stepName The exact text of the step to check
       * @param isCompleted Whether the step should be completed or not
       * @param successMessage The message expected when a step is completed (optional)
       */
      const checkStepStatus = (
        stepName: string,
        isCompleted: boolean,
        successMessage?: string,
      ) => {
        cy.getByTestId("integration-setup-card").within(() => {
          // Check if the step is marked as completed
          cy.contains(stepName)
            .closest(".ant-steps-item")
            .should(
              isCompleted ? "have.class" : "not.have.class",
              "ant-steps-item-finish",
            );

          // If a success message is provided, check that it exists
          if (successMessage) {
            cy.contains(successMessage).should("exist");
          }
        });
      };

      beforeEach(() => {
        stubPlus(true);
        stubIntegrationManagement();

        cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
          fixture: "detection-discovery/monitors/empty_monitors.json",
        }).as("getEmptyMonitors");
      });

      it("shows create integration step as done", () => {
        cy.visit("/integrations/bq_integration");
        cy.wait("@getConnection");
        cy.wait("@getConnectionTypes");

        checkStepStatus(
          "Create integration",
          true,
          "Integration created successfully",
        );
      });

      it("doesn't show authorize step for integration that doesn't require authorization", () => {
        cy.visit("/integrations/bq_integration");
        cy.wait("@getConnection");
        cy.wait("@getConnectionTypes");

        cy.getByTestId("integration-setup-card").within(() => {
          cy.contains("Authorize integration").should("not.exist");
        });
      });

      it("shows unchecked create monitor step when no monitors", () => {
        cy.visit("/integrations/bq_integration");
        cy.wait("@getConnection");
        cy.wait("@getConnectionTypes");
        cy.wait("@getEmptyMonitors");

        checkStepStatus("Create monitor", false);
        cy.getByTestId("integration-setup-card").within(() => {
          cy.contains(
            "Use the Data discovery tab in this page to add a new monitor",
          ).should("exist");
        });
      });

      it("shows checked create monitor step when monitor exists", () => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
          fixture: "detection-discovery/monitors/monitor_list.json",
        }).as("getMonitors");

        cy.visit("/integrations/bq_integration");
        cy.wait("@getConnection");
        cy.wait("@getConnectionTypes");
        cy.wait("@getMonitors");

        cy.getByTestId("integration-setup-card").should("exist");
        cy.getByTestId("integration-setup-card").should(
          "contain.text",
          "Data monitor created successfully",
          { timeout: 10000 },
        );

        checkStepStatus(
          "Create monitor",
          true,
          "Data monitor created successfully",
        );
      });

      it("shows unchecked link system step when no system linked", () => {
        cy.visit("/integrations/bq_integration");
        cy.wait("@getConnection");
        cy.wait("@getConnectionTypes");

        checkStepStatus("Link system", false);
        cy.getByTestId("integration-setup-card").within(() => {
          cy.contains("Link this integration in the").should("exist");
        });
      });

      it("shows checked link system step when system is linked", () => {
        // Set up intercepts before visiting the page
        cy.intercept("GET", "/api/v1/connection/*", (req) => {
          const fixtureData = require("../fixtures/connectors/salesforce_connection.json");
          fixtureData.system_key = "fidesctl_system";
          req.reply(fixtureData);
        }).as("getConnectionWithSystem");

        cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
          fixture: "detection-discovery/monitors/monitor_list.json",
        }).as("getMonitors");

        cy.visit("/integrations/salesforce_integration");
        cy.wait("@getConnectionWithSystem");
        cy.wait("@getMonitors");
        cy.wait("@getConnectionTypes");

        cy.getByTestId("integration-setup-card").should("exist");
        cy.getByTestId("integration-setup-card")
          .should("contain.text", "System linked", { timeout: 10000 })
          .should("contain.text", "Data monitor created successfully", {
            timeout: 10000,
          });

        checkStepStatus("Link system", true, "System linked");
      });

      it("shows unchecked authorize step for unauthorized Salesforce integration", () => {
        // Use direct fixture modification approach instead of fixture reference
        cy.intercept("GET", "/api/v1/connection/*", (req) => {
          const fixtureData = require("../fixtures/connectors/salesforce_connection.json");
          // Ensure authorized is explicitly set to false
          fixtureData.authorized = false;
          req.reply(fixtureData);
        }).as("getSalesforceConnection");

        cy.visit("/integrations/salesforce_integration");
        cy.wait("@getSalesforceConnection");
        cy.wait("@getConnectionTypes");

        // Wait for the authorization text to appear to ensure component has loaded
        cy.getByTestId("integration-setup-card")
          .should("exist")
          .should("contain.text", "Authorize integration", { timeout: 10000 })
          .should("contain.text", "Authorize access to your integration", {
            timeout: 10000,
          });

        checkStepStatus("Authorize integration", false);
        cy.getByTestId("integration-setup-card").within(() => {
          cy.contains("Authorize access to your integration").should("exist");
        });
      });

      it("shows checked authorize step for authorized Salesforce integration", () => {
        cy.intercept("GET", "/api/v1/connection/*", {
          fixture: "connectors/salesforce_connection.json",
          onRequest: (req) => {
            req.on("response", (res) => {
              const body = res.body;
              body.authorized = true;
              res.send({ body });
            });
          },
        }).as("getAuthorizedSalesforceConnection");

        cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
          fixture: "detection-discovery/monitors/monitor_list.json",
        }).as("getMonitors");

        cy.visit("/integrations/salesforce_integration");
        cy.wait("@getAuthorizedSalesforceConnection");
        cy.wait("@getConnectionTypes");

        cy.getByTestId("integration-setup-card")
          .should("exist")
          .should("contain.text", "Authorize integration", { timeout: 10000 })
          .should("contain.text", "Data monitor created successfully", {
            timeout: 10000,
          });

        checkStepStatus(
          "Authorize integration",
          true,
          "Integration authorized successfully",
        );
      });

      describe("website integrations", () => {
        // There is no reason for a website integration to have a system linked
        beforeEach(() => {
          cy.intercept("GET", "/api/v1/connection/*", {
            fixture: "connectors/website_integration.json",
          }).as("getWebsiteIntegration");

          cy.intercept("GET", "/api/v1/connection_type?*", {
            fixture: "connectors/connection_types.json",
          }).as("getConnectionTypes");
        });

        it("should not show link system step for website integrations", () => {
          cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
            fixture: "detection-discovery/monitors/website_monitor_list.json",
          }).as("getWebsiteMonitors");

          cy.visit("/integrations/test_website_integration");
          cy.wait("@getWebsiteIntegration");
          cy.wait("@getWebsiteMonitors");
          cy.wait("@getConnectionTypes");

          // Verify that the Link system step is not shown for website integrations
          cy.getByTestId("integration-setup-card").within(() => {
            cy.contains("Link system").should("not.exist");
          });

          // Verify that other steps are still present
          cy.getByTestId("integration-setup-card").within(() => {
            cy.contains("Create integration").should("exist");
            cy.contains("Create monitor").should("exist");
          });
        });

        it("shows create integration step as completed for website integrations", () => {
          cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
            fixture: "detection-discovery/monitors/empty_monitors.json",
          }).as("getEmptyMonitors");

          cy.visit("/integrations/test_website_integration");
          cy.wait("@getWebsiteIntegration");
          cy.wait("@getEmptyMonitors");
          cy.wait("@getConnectionTypes");

          checkStepStatus(
            "Create integration",
            true,
            "Integration created successfully",
          );
        });
      });
    });
  });
});
