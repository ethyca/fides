import {
  stubLocations,
  stubPlus,
  stubSharedMonitorConfig,
  stubSystemCrud,
  stubTaxonomyEntities,
} from "cypress/support/stubs";
import { AntSelect } from "fidesui";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

describe("Integration management for data detection & discovery", () => {
  beforeEach(() => {
    cy.login();
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
      cy.getByTestId("integration-tabs").should("exist");
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

    describe("list view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/connection?*", {
          fixture: "connectors/bigquery_connection_list.json",
        }).as("getConnections");
        cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
        cy.wait("@getConnections");
      });

      it("should show a list of integrations", () => {
        cy.getByTestId("integration-info-bq_integration").should("exist");
        cy.getByTestId("empty-state").should("not.exist");
      });

      it("should be able to test connections by clicking the button", () => {
        cy.intercept("GET", "/api/v1/connection/bq_integration", {
          fixture: "connectors/bigquery_connection.json",
        }).as("getConnection");
        cy.getByTestId("integration-info-bq_integration")
          .should("exist")
          .within(() => {
            cy.getByTestId("test-connection-btn").click();
            cy.wait("@testConnection");
          });
      });

      it("should navigate to management page when 'manage' button is clicked", () => {
        cy.intercept("GET", "/api/v1/connection/bq_integration", {
          fixture: "connectors/bigquery_connection.json",
        }).as("getConnection");
        cy.getByTestId("integration-info-bq_integration").within(() => {
          cy.getByTestId("configure-btn").click();
          cy.url().should("contain", "/bq_integration");
        });
      });

      it("should paginate integrations", () => {
        cy.intercept("GET", "/api/v1/connection?*&page=1*", {
          fixture: "connectors/list_page_1_50_items.json",
        }).as("getConnectionsPage1");
        cy.intercept("GET", "/api/v1/connection?*&page=2*", {
          fixture: "connectors/list_page_2_30_items.json",
        }).as("getConnectionsPage2");
        cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
        cy.wait("@getConnectionsPage1");

        // Set up intercept for page 2

        // Check that pagination controls are visible
        cy.getByTestId("pagination-controls").should("exist");

        // Check that the correct number of items are displayed (50 items on page 1)
        cy.get("[data-testid^='integration-info-']").should("have.length", 50);

        // Verify we're on page 1 of 2
        cy.getByTestId("pagination-controls").should("contain", "1");
        cy.getByTestId("pagination-controls").should("contain", "2");

        // Click to go to page 2
        cy.getByTestId("pagination-controls").within(() => {
          cy.contains("2").click();
        });
        cy.wait("@getConnectionsPage2");

        // Check that the correct number of items are displayed (30 items on page 2)
        cy.get("[data-testid^='integration-info-']").should("have.length", 30);

        // Verify the first item on page 2 is different from page 1
        cy.getByTestId("integration-info-snowflake_connector_11").should(
          "exist",
        );
      });
    });

    describe("adding an integration", () => {
      beforeEach(() => {
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
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-bq_placeholder").within(() => {
            cy.getByTestId("configure-btn").click();
          });
        });
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
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-bq_placeholder").within(() => {
            cy.getByTestId("configure-btn").click();
          });
        });
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

      it("should be able to add a new integration without secrets", () => {
        cy.intercept("PATCH", "/api/v1/connection", { statusCode: 200 }).as(
          "patchConnection",
        );
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("integration-info-manual_placeholder").within(() => {
            cy.getByTestId("configure-btn").click();
          });
        });
        cy.getByTestId("input-name").type("Manual Integration Test");
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
      });
    });
  });

  describe("detail view", () => {
    beforeEach(() => {
      stubPlus(true);
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
      cy.getByTestId("tab-Data discovery").click();
      cy.wait("@getEmptyMonitors");
      cy.getByTestId("no-results-notice").should("exist");
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
        cy.getByTestId("tab-Data discovery").click();
        cy.wait("@getMonitors");
        stubSharedMonitorConfig();
      });

      it("shows a table of monitors", () => {
        cy.getByTestId("row-test monitor 1").should("exist");
        // scan status column
        cy.getByTestId("row-test monitor 1-col-monitor_status").should(
          "contain",
          "Scanning",
        );
        cy.getByTestId("row-test monitor 2-col-monitor_status").within(() => {
          cy.getByTestId("tag-success").should("exist");
        });
        cy.getByTestId("row-test monitor 3-col-monitor_status").within(() => {
          cy.getByTestId("tag-error").should("exist").click();
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
        cy.getByTestId("row-test monitor 1").within(() => {
          cy.getByTestId("edit-monitor-btn").click();
        });
        cy.getByTestId("input-name").should("have.value", "test monitor 1");
        cy.getByTestId("input-execution_start_date")
          .should("have.prop", "value")
          .should("match", /2024-06-04T[0-9][0-9]:11/); // because timzones
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

      it("can edit an existing monitor by clicking the table row", () => {
        cy.getByTestId("row-test monitor 2").click();
        cy.getByTestId("input-name").should("have.value", "test monitor 2");
        cy.getByTestId("controlled-select-execution_frequency").should(
          "contain",
          "Weekly",
        );
      });

      it("can execute a monitor", () => {
        cy.getByTestId("row-test monitor 1").within(() => {
          cy.getByTestId("action-Scan").click();
        });
        cy.wait("@executeMonitor");
      });

      it("can delete a monitor", () => {
        cy.getByTestId("row-test monitor 1").within(() => {
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
        cy.getByTestId("row-test monitor 1").within(() => {
          cy.getByTestId("toggle-switch").click();
        });
        cy.wait("@putMonitor");
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
        cy.getByTestId("tab-Data discovery").click();
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
        cy.getByTestId("tab-Data discovery").click();
        cy.wait("@getMonitors");
      });

      it("should render the website monitor list", () => {
        cy.getByTestId("monitor-description").contains(
          "Configure your website monitor",
        );
        cy.getByTestId("row-test website monitor-col-name").should(
          "contain",
          "test website monitor",
        );
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
        cy.getByTestId("row-test website monitor").click();
        cy.getByTestId("input-name")
          .should("have.value", "test website monitor")
          .clear()
          .type("A different name");
        cy.getByTestId("save-btn").click();
        cy.wait("@putMonitor").then((interception) => {
          expect(interception.request.body.name).to.equal("A different name");
        });
      });
    });
  });
});
