import { stubPlus, stubSystemCrud } from "cypress/support/stubs";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

describe("Integration management for data detection & discovery", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/connection/*/test", {
      statusCode: 200,
      body: {
        test_status: "succeeded",
      },
    }).as("testConnection");
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
      cy.intercept("GET", "/api/v1/connection*", {
        fixture: "connectors/empty_list.json",
      }).as("getConnections");
      cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
      cy.wait("@getConnections");
      cy.getByTestId("empty-state").should("exist");
    });

    describe("list view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/connection*", {
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
        cy.getByTestId("integration-info-bq_integration").within(() => {
          cy.getByTestId("test-connection-btn").click();
          cy.wait("@testConnection");
        });
      });

      it("should navigate to management page when 'manage' button is clicked", () => {
        cy.getByTestId("integration-info-bq_integration").within(() => {
          cy.getByTestId("configure-btn").click();
          cy.url().should("contain", "/bq_integration");
        });
      });
    });

    describe("adding an integration", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/connection*", {
          fixture: "connectors/bigquery_connection_list.json",
        }).as("getConnections");
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

      it("should be able to add a new BigQuery integration", () => {
        cy.intercept("PATCH", "/api/v1/connection").as("patchConnection");
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("configure-btn").click();
        });
        cy.getByTestId("input-name").type("test name");
        cy.getByTestId("input-description").type("test description");
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
      });

      it("should be able to add a new integration with secrets", () => {
        cy.intercept("PATCH", "/api/v1/connection").as("patchConnection");
        cy.intercept("PUT", "/api/v1/connection/*/secret*").as(
          "putConnectionSecrets"
        );
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("configure-btn").click();
        });
        cy.getByTestId("input-name").type("test name");
        cy.getByTestId("input-keyfile_creds").type(`{"credentials": "test"}`, {
          parseSpecialCharSequences: false,
        });
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
        cy.wait("@putConnectionSecrets");
      });

      it("should be able to add a new integration associated with a system", () => {
        stubSystemCrud();
        cy.intercept("PATCH", "/api/v1/system/*/connection").as(
          "patchSystemConnection"
        );
        cy.intercept("GET", "/api/v1/system", {
          fixture: "systems/systems.json",
        }).as("getSystems");
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("configure-btn").click();
        });
        cy.getByTestId("input-name").type("test name");
        cy.selectOption("input-system_fides_key", "Fidesctl System");
        cy.getByTestId("save-btn").click();
        cy.wait("@patchSystemConnection");
      });
    });
  });

  describe("detail view", () => {
    beforeEach(() => {
      stubPlus(true);
      cy.intercept("GET", "/api/v1/connection/*", {
        fixture: "connectors/bigquery_connection.json",
      }).as("getConnection");
      cy.visit("/integrations/bq_integration");
    });

    it("can test the connection", () => {
      cy.getByTestId("test-connection-btn").click();
      cy.wait("@testConnection");
    });

    it("can edit integration with the modal", () => {
      cy.intercept("PATCH", "/api/v1/connection").as("patchConnection");
      cy.getByTestId("manage-btn").click();
      cy.getByTestId("input-system_fides_key").should("not.exist");
      cy.getByTestId("input-name")
        .should("have.value", "BQ Integration")
        .clear()
        .type("A different name");
      cy.getByTestId("save-btn").click();
      cy.wait("@patchConnection");
    });

    it("shows an empty state in 'data discovery' tab when no monitors are configured", () => {
      cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
        fixture: "detection-discovery/monitors/empty_monitors.json",
      }).as("getEmptyMonitors");
      cy.getByTestId("tab-Data discovery").click();
      cy.wait("@getEmptyMonitors");
      cy.getByTestId("no-results-notice").should("exist");
    });

    describe("data discovery tab", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor*", {
          fixture: "detection-discovery/monitors/monitor_list.json",
        }).as("getMonitors");
        cy.intercept("GET", "/api/v1/plus/discovery-monitor/*/databases", {
          fixture: "detection-discovery/monitors/database_list.json",
        }).as("getDatabases");
        cy.getByTestId("tab-Data discovery").click();
        cy.wait("@getMonitors");
      });

      it("shows a table of monitors", () => {
        cy.getByTestId("row-test monitor 1").should("exist");
      });

      it("can configure a new monitor", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*", {
          statusCode: 200,
          body: {
            name: "A new monitor",
            key: "a_new_monitor",
            connection_config_key: "bq_integration",
            classify_params: {
              possible_targets: null,
              top_n: 5,
              remove_stop_words: false,
              pii_threshold: 0.4,
              num_samples: 25,
              num_threads: 1,
            },
            databases: [],
            execution_start_date: "2034-06-03T00:00:00.000Z",
            execution_frequency: "Daily",
          },
        }).as("putMonitor");
        cy.getByTestId("add-monitor-btn").click();
        cy.getByTestId("input-name").type("A new monitor");
        cy.getByTestId("input-execution_start_date").type("2034-06-03");
        cy.selectOption("input-execution_frequency", "Daily");
        cy.getByTestId("next-btn").click();
        cy.wait("@putMonitor").then((interception) => {
          expect(interception.request.body).to.eql({
            name: "A new monitor",
            connection_config_key: "bq_integration",
            classify_params: {
              num_threads: 1,
              num_samples: 25,
            },
            execution_start_date: "2034-06-03T00:00:00.000Z",
            execution_frequency: "Daily",
          });
        });
        cy.getByTestId("select-all").click();
        cy.getByTestId("save-btn").click();
        cy.wait("@putMonitor").then((interception) => {
          expect(interception.request.body.databases).to.length(3);
        });
        cy.wait("@getMonitors");
      });

      it("can edit an existing monitor by clicking the edit button", () => {
        cy.intercept("PUT", "/api/v1/plus/discovery-monitor*").as("putMonitor");
        cy.getByTestId("row-test monitor 1").within(() => {
          cy.getByTestId("edit-monitor-btn").click();
        });
        cy.getByTestId("input-name").should("have.value", "test monitor 1");
        cy.getByTestId("next-btn").click();
        cy.getByTestId("prj-bigquery-000001-checkbox").should(
          "have.attr",
          "data-checked"
        );
        cy.getByTestId("prj-bigquery-000003-checkbox").should(
          "not.have.attr",
          "data-checked"
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
        cy.getByTestId("input-execution_start_date").should("not.exist");
        cy.getSelectValueContainer("input-execution_frequency").should(
          "contain",
          "Weekly"
        );
      });
    });
  });
});
