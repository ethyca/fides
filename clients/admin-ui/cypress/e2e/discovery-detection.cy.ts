import {
  stubPlus,
  stubStagedResourceActions,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import {
  DATA_DETECTION_ROUTE,
  DATA_DISCOVERY_ROUTE,
  DETECTION_DISCOVERY_ACTIVITY_ROUTE,
} from "~/features/common/nav/routes";
import { RoleRegistryEnum } from "~/types/api/models/RoleRegistryEnum";

describe("discovery and detection", () => {
  beforeEach(() => {
    cy.login();
    cy.assumeRole(RoleRegistryEnum.OWNER);
    stubPlus(true);
    stubStagedResourceActions();
    stubTaxonomyEntities();
    cy.intercept("GET", "/api/v1/config*", {
      body: {
        detection_discovery: {
          monitor_celery_tasks_enabled: true,
          website_monitor_enabled: true,
        },
      },
    });
  });

  describe("default tab behavior without hash", () => {
    it("should default to action-required tab for detection results", () => {
      cy.intercept(
        "GET",
        "/api/v1/plus/discovery-monitor/results?*diff_status=addition&diff_status=removal*",
        {
          fixture: "detection-discovery/results/detection/dataset-list.json",
        },
      ).as("getDetectionResultsWithActionRequiredFilters");

      cy.visit(DATA_DETECTION_ROUTE);
      cy.wait("@getDetectionResultsWithActionRequiredFilters");

      // Verify the action-required tab is active (check parent div)
      cy.getAntTab("Action Required")
        .parent()
        .should("have.class", "ant-tabs-tab-active");
    });

    it("should default to action-required tab for discovery results", () => {
      cy.intercept(
        "GET",
        "/api/v1/plus/discovery-monitor/results?*diff_status=classification_addition&diff_status=classification_update*",
        {
          fixture: "detection-discovery/results/discovery/dataset-list.json",
        },
      ).as("getDiscoveryResultsWithActionRequiredFilters");

      cy.visit(DATA_DISCOVERY_ROUTE);
      cy.wait("@getDiscoveryResultsWithActionRequiredFilters");

      // Verify the action-required tab is active (check parent div)
      cy.getAntTab("Action Required")
        .parent()
        .should("have.class", "ant-tabs-tab-active");
    });
  });

  describe("activity table", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
        fixture: "detection-discovery/results/activity-results.json",
      }).as("getActivityResults");
      cy.visit(DETECTION_DISCOVERY_ACTIVITY_ROUTE);
      cy.wait("@getActivityResults");
    });

    describe("additions", () => {
      it("should show addition icon", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000000.test_dataset_1-col-name",
        ).within(() => {
          cy.getByTestId("add-icon").should("exist");
        });
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000000.test_dataset_1-col-status",
        ).should("contain", "Pending review");
      });

      it("should be able to monitor or ignore", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000000.test_dataset_1-col-action",
        ).within(() => {
          cy.getByTestId("action-Monitor").click();
          cy.wait("@confirmResource");
        });
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000000.test_dataset_1-col-action",
        ).within(() => {
          cy.getByTestId("action-Ignore").click();
          cy.wait("@ignoreResource");
        });
      });

      it("should navigate to detection view on click", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000000.test_dataset_1",
        ).click();
        cy.url().should("contain", "detection");
      });
    });

    describe("changes", () => {
      it("should show change icon", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000001.test_dataset_2-col-name",
        ).within(() => {
          cy.getByTestId("change-icon").should("exist");
        });
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000001.test_dataset_2-col-status",
        ).should("contain", "Pending review");
      });

      it("should be able to monitor or ignore", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000001.test_dataset_2-col-action",
        ).within(() => {
          cy.getByTestId("action-Monitor").click();
          cy.wait("@confirmResource");
        });
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000001.test_dataset_2-col-action",
        ).within(() => {
          cy.getByTestId("action-Ignore").click();
          cy.wait("@ignoreResource");
        });
      });

      it("should navigate to detection view on click", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000001.test_dataset_2",
        ).click();
        cy.url().should("contain", "detection");
      });
    });

    describe("removals", () => {
      it("should show removal icon", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000001.test_dataset_3-col-name",
        ).within(() => {
          cy.getByTestId("remove-icon").should("exist");
        });
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000000.test_dataset_1-col-status",
        ).should("contain", "Pending review");
      });

      it("should only be able to ignore", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000001.test_dataset_3-col-action",
        ).within(() => {
          cy.getByTestId("action-Confirm").should("not.exist");
          cy.getByTestId("action-Monitor").should("not.exist");
          cy.getByTestId("action-Ignore").click();
          cy.wait("@ignoreResource");
        });
      });

      it("should navigate to detection view on click", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000001.test_dataset_3",
        ).click();
        cy.url().should("contain", "detection");
      });
    });

    describe("classifications", () => {
      it("should show classification icon", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000002.test_dataset_4-col-name",
        ).within(() => {
          cy.getByTestId("classify-icon").should("exist");
        });
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000002.test_dataset_4-col-status",
        ).should("contain", "Pending review");
      });

      it("should be able to confirm or ignore", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000002.test_dataset_4-col-action",
        ).within(() => {
          cy.getByTestId("action-Confirm").click();
          cy.wait("@promoteResource");
        });
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000002.test_dataset_4-col-action",
        ).within(() => {
          cy.getByTestId("action-Ignore").click();
          cy.wait("@ignoreResource");
        });
      });

      it("should navigate to discovery view on row click", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-000001.test_dataset_2",
        ).click();
        cy.url().should("contain", "discovery");
      });
    });
  });

  describe("detection tables", () => {
    describe("activity view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
          fixture: "detection-discovery/results/detection/dataset-list.json",
        }).as("getDetectionActivity");
        cy.visit(DATA_DETECTION_ROUTE);
      });

      it("should navigate to a table view on click", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1",
        ).click();
        cy.url().should("contain", "test_dataset_1");
        cy.getByTestId("results-breadcrumb").should(
          "contain",
          "test_dataset_1",
        );
      });
    });

    describe("table-level view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
          fixture: "detection-discovery/results/detection/table-list.json",
        }).as("getFilteredDetectionTables");
        cy.intercept(
          "GET",
          "/api/v1/plus/discovery-monitor/results?diff_status=monitored*",
          {
            fixture:
              "detection-discovery/results/detection/table-list-monitored-tab-filter.json",
          },
        ).as("getAllMonitoredTables");
        cy.intercept(
          "GET",
          "/api/v1/plus/discovery-monitor/results?diff_status=muted*",
          {
            fixture:
              "detection-discovery/results/detection/table-list-unmonitored-tab-filter.json",
          },
        ).as("getAllMutedTables");
        cy.visit(
          `${DATA_DETECTION_ROUTE}/my_bigquery_monitor.prj-bigquery-418515.test_dataset_1`,
        );
      });

      it("should show columns for tables with changes", () => {
        cy.getByTestId("name-header").should("contain", "Table name");
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20",
        ).within(() => {
          cy.getByTestId(
            "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20-col-name",
          ).should("contain", "consent-reports-20");
        });
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-18",
        ).should("exist");
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-18",
        ).within(() => {
          cy.getByTestId("action-Monitor").click();
          cy.wait("@confirmResource");
        });
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-19",
        ).should("exist");
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-21",
        ).should("not.exist");
      });

      it("should navigate to field view on row click", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20",
        ).click();
        cy.url().should("contain", "consent-reports-20");
        cy.getByTestId("results-breadcrumb").should(
          "contain",
          "consent-reports-20",
        );
      });

      describe("Tab filter views", () => {
        it("should be able to switch to monitored tab", () => {
          cy.getAntTab("Monitored").click({ force: true });
          cy.wait("@getAllMonitoredTables");

          cy.getByTestId(
            "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20-col-status",
          ).should("contain", "Monitoring");
        });

        it("should allow monitored tables to be muted", () => {
          cy.getAntTab("Monitored").click({ force: true });
          cy.getByTestId(
            "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20-col-actions",
          ).within(() => {
            cy.getByTestId("action-Ignore").click();
            cy.wait("@ignoreResource");
          });
        });

        it("should be able to switch to unmonitored tab", () => {
          cy.getAntTab("Unmonitored").click({ force: true });
          cy.wait("@getAllMutedTables");

          cy.getByTestId(
            "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-21-col-status",
          ).should("contain", "Unmonitored");
        });

        it("should allow muted tables to be monitored", () => {
          cy.getAntTab("Unmonitored").click({ force: true });
          cy.getByTestId(
            "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-21-col-actions",
          ).within(() => {
            cy.getByTestId("action-Monitor").click();
            cy.wait("@confirmResource");
          });
        });
      });
    });

    describe("field-level view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
          fixture: "detection-discovery/results/detection/field-list.json",
        }).as("getDetectionFields");
        cy.visit(
          `${DATA_DETECTION_ROUTE}/my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20`,
        );
        cy.wait("@getDetectionFields");
      });

      it("should show columns for fields", () => {
        cy.getByTestId("fidesTable-body").should("exist");
        cy.getByTestId("column-name").should("contain", "Field name");
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.Created-col-name",
        ).should("contain", "Created");
      });

      it("should allow navigation via row clicking on nested fields", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.address",
        ).click();
        cy.url().should("contain", "address");
      });

      it("should not allow navigation via row clicking on non-nested fields", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.User_geography",
        ).click();
        cy.url().should("not.contain", "User_geography");
      });
    });
  });

  describe("discovery tables", () => {
    describe("activity view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
          fixture: "detection-discovery/results/discovery/dataset-list.json",
        });
        cy.visit(DATA_DISCOVERY_ROUTE);
      });

      it("should navigate to table view on row click", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1",
        ).click();
        cy.url().should("contain", "test_dataset_1");
        cy.getByTestId("results-breadcrumb").should(
          "contain",
          "test_dataset_1",
        );
      });

      it("should be able to reclassify", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1",
        ).within(() => {
          cy.getByTestId("actions-overflow-btn").click();
          cy.getByTestId("action-reclassify").click({ force: true });
          cy.wait("@confirmResource");
        });
      });
    });

    describe("table-level view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
          fixture: "detection-discovery/results/discovery/table-list.json",
        });
        cy.visit(
          `${DATA_DISCOVERY_ROUTE}/my_bigquery_monitor.prj-bigquery-418515.test_dataset_1`,
        );
      });

      it("should show columns for tables", () => {
        cy.getByTestId("column-select").should("exist");
        cy.getByTestId("bulk-actions-menu").should("not.exist");
      });

      it("should navigate to field view on row click", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20",
        ).click();
        cy.url().should("contain", "consent-reports-20");
        cy.getByTestId("results-breadcrumb").should(
          "contain",
          "consent-reports-20",
        );
      });

      it("should show bulk actions when tables are selected", () => {
        cy.getByTestId("select-consent-reports-20").click();
        cy.getByTestId("bulk-actions-menu").should("contain", "1 selected");
        cy.getByTestId("bulk-actions-menu").within(() => {
          cy.getByTestId("action-Confirm").click();
          cy.wait("@promoteResource");
        });
      });
    });

    describe("field-level view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
          fixture: "detection-discovery/results/discovery/field-list.json",
        });
        cy.visit(
          `${DATA_DISCOVERY_ROUTE}/my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports`,
        );
      });

      it("should show columns for fields", () => {
        cy.getByTestId("column-classifications").should("exist");
      });

      it("should show bulk actions for the containing table", () => {
        cy.getByTestId("bulk-actions-menu").within(() => {
          cy.getByTestId("action-Confirm all").click();
          cy.wait("@promoteResource");
        });
      });

      it("should allow navigation via row clicking on nested fields", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.address-col-name",
        ).click();
        cy.url().should("contain", "address");
      });

      it("should not allow navigation via row clicking on non-nested fields", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.User_geography-col-name",
        ).click();
        cy.url().should("not.contain", "User_geography");
      });

      it("allows classifications to be changed using the dropdown", () => {
        stubTaxonomyEntities();
        cy.intercept("PATCH", "/api/v1/plus/discovery-monitor/*/results").as(
          "patchClassification",
        );
        cy.getByTestId("classification-user.contact.phone_number").click();
        cy.getByTestId("taxonomy-select").antSelect("system");
        cy.wait("@patchClassification");
      });

      it("shows user-assigned categories and allows adding new categories", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.Test-col-classifications",
        ).within(() => {
          cy.getByTestId(
            "user-classification-user.contact.phone_number",
          ).should("exist");
          cy.getByTestId("taxonomy-add-btn").click();
          cy.get(".select-wrapper").should("exist");
        });
      });

      it("shows 'None' when no categories are assigned", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.No_categories-col-classifications",
        ).within(() => {
          cy.getByTestId("no-classifications").should("exist");
          cy.getByTestId("taxonomy-add-btn").should("exist");
        });
      });

      it("doesn't allow adding categories on fields with subfields", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.address-col-classifications",
        ).within(() => {
          cy.getByTestId("no-classifications").should("exist");
          cy.getByTestId("taxonomy-add-btn").should("not.exist");
        });
      });

      it("doesn't allow reclassifying fields", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.address-col-actions",
        ).within(() => {
          cy.getByTestId("action-reclassify").should("not.exist");
        });
      });
    });

    describe("nested-field-level view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
          fixture:
            "detection-discovery/results/discovery/nested-field-list.json",
        }).as("getNestedDetectionFields");
        cy.visit(
          `${DATA_DETECTION_ROUTE}/my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.address`,
        );
        cy.wait("@getNestedDetectionFields");
      });

      it("should show columns for nested fields", () => {
        cy.getByTestId("fidesTable-body").should("exist");
        cy.getByTestId("column-name").should("contain", "Field name");
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.address.zip-col-name",
        ).should("contain", "zip");
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.address.street.line_1-col-name",
        ).should("contain", "street.line_1");
      });

      it("should not allow navigation via row clicking", () => {
        cy.getByTestId(
          "row-my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.address.street.line_1",
        ).click();
        cy.url().should("not.contain", "street");
      });
    });
  });

  describe("without a db layer", () => {
    it("shows resource name for resources that are not subfields", () => {
      cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
        fixture: "detection-discovery/results/no-db-layer/field-list.json",
      }).as("getFields");
      cy.visit(
        `${DATA_DISCOVERY_ROUTE}/dynamo_monitor.test_dataset_5.test_table_1`,
      );
      cy.getByTestId(
        "row-dynamo_monitor.test_dataset_5.test_table_1.test_field_1-col-name",
      ).should("contain", "test_field_1");
    });

    it("shows subfield names in dot notation", () => {
      cy.intercept("GET", "/api/v1/plus/discovery-monitor/results?*", {
        fixture:
          "detection-discovery/results/no-db-layer/nested-field-list.json",
      }).as("getFields");
      cy.visit(
        `${DATA_DISCOVERY_ROUTE}/my_bigquery_monitor.prj-bigquery-418515.test_dataset_1.consent-reports-20.address`,
      );
      cy.getByTestId(
        "row-dynamo_monitor.test_dataset_5.test_table_1.address.zip-col-name",
      ).should("contain", "zip");
      cy.getByTestId(
        "row-dynamo_monitor.test_dataset_5.test_table_1.address.street.line_1-col-name",
      ).should("contain", "street.line_1");
      // should still see correct name when top_level_field_urn is not provided
      cy.getByTestId(
        "row-dynamo_monitor.test_dataset_5.test_table_1.address.street.line_2-col-name",
      ).should("contain", "street.line_2");
    });
  });
});
