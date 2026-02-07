import {
  stubInfrastructureSystems,
  stubInfrastructureSystemsBulkActions,
  stubInfrastructureSystemsFilters,
  stubPlus,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";

describe("Action center infrastructure systems", () => {
  const monitorId = "my_infrastructure_monitor_1";
  const testUrn = "urn:okta:app:12345678-1234-1234-1234-123456789012";

  describe("error handling", () => {
    beforeEach(() => {
      cy.login();
      stubPlus(true);
      stubTaxonomyEntities();
      cy.intercept(
        "GET",
        `/api/v1/plus/identity-provider-monitors/${monitorId}/results*`,
        {
          statusCode: 500,
          body: { detail: "Internal server error" },
        },
      ).as("getIdentityProviderMonitorResultsError");
    });

    it("should display error page when fetching infrastructure systems fails", () => {
      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getIdentityProviderMonitorResultsError");

      cy.getByTestId("error-page-result").should("exist");
      cy.getByTestId("error-page-result").within(() => {
        cy.contains("Error 500").should("exist");
        cy.contains("Internal server error").should("exist");
        cy.contains("Reload").should("exist");
      });
    });
  });

  describe("data use management", () => {
    beforeEach(() => {
      cy.login();
      stubPlus(true);
      stubTaxonomyEntities();
      stubInfrastructureSystems();
    });

    it("should allow adding a data use to an infrastructure system", () => {
      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get(`[data-classification-select="${testUrn}"]`).within(() => {
        cy.get("button[aria-label='Add data use']").click({ force: true });
      });

      cy.get(`[data-classification-select="${testUrn}"]`).antSelect(0);

      cy.wait("@updateInfrastructureSystemDataUses").then((interception) => {
        expect(interception.request.body).to.deep.equal({
          urn: testUrn,
          user_assigned_data_uses: ["marketing.advertising", "analytics"],
        });
      });
    });

    it("should allow removing a data use from an infrastructure system", () => {
      const slackUrn = "urn:okta:app:another-app";

      cy.intercept(
        "PATCH",
        `/api/v1/plus/identity-provider-monitors/${monitorId}/results/${slackUrn}`,
        {
          statusCode: 200,
          body: {
            urn: slackUrn,
            user_assigned_data_uses: ["marketing.advertising"],
          },
        },
      ).as("updateSlackSystemDataUses");

      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get(`[data-classification-select="${slackUrn}"]`).within(() => {
        cy.get(".ant-tag").filter(":contains('Analytics')").should("exist");
        cy.get(".ant-tag")
          .filter(":contains('Analytics')")
          .within(() => {
            cy.get("button").click({ force: true });
          });
      });

      cy.wait("@updateSlackSystemDataUses").then((interception) => {
        expect(interception.request.body).to.deep.equal({
          urn: slackUrn,
          user_assigned_data_uses: ["marketing.advertising"],
        });
      });
    });

    it("should handle error when updating data uses fails", () => {
      stubInfrastructureSystems({
        patchStatus: 500,
        patchResponse: { detail: "Internal server error" },
      });

      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get(`[data-classification-select="${testUrn}"]`).within(() => {
        cy.get("button[aria-label='Add data use']").click({ force: true });
      });

      cy.get(`[data-classification-select="${testUrn}"]`).antSelect(0);

      cy.wait("@updateInfrastructureSystemDataUses");

      cy.get(".ant-message-error", { timeout: 5000 }).should("exist");
      cy.get(".ant-message-error").should("contain", "Internal server error");
    });

    it("should not add duplicate data uses", () => {
      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      // cy.get(`[data-classification-select="${testUrn}"]`).within(() => {
      //   cy.get("button[aria-label='Add data use']").click({ force: true });
      // });

      cy.get(`[data-classification-select="${testUrn}"]`)
        .find("input")
        .focus()
        .type("marketing.advertising");

      cy.get(`[data-classification-select="${testUrn}"]`).antSelect(0);

      cy.get("@updateInfrastructureSystemDataUses.all").should(
        "have.length",
        0,
      );
    });

    it("should allow removing the last data use", () => {
      stubInfrastructureSystems({
        fixture:
          "detection-discovery/results/infrastructure-systems-single-data-use.json",
      });

      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get(`[data-classification-select="${testUrn}"]`).within(() => {
        cy.get(".ant-tag").filter(":contains('Marketing')").should("exist");
        cy.get(".ant-tag")
          .filter(":contains('Marketing')")
          .within(() => {
            cy.get("button").click({ force: true });
          });
      });

      cy.wait("@updateInfrastructureSystemDataUses").then((interception) => {
        expect(interception.request.body).to.deep.equal({
          urn: testUrn,
          user_assigned_data_uses: [],
        });
      });
    });
  });

  describe("search functionality", () => {
    beforeEach(() => {
      cy.login();
      stubPlus(true);
      stubTaxonomyEntities();
      stubInfrastructureSystemsFilters(monitorId);
    });

    it("should update query parameter when searching", () => {
      stubInfrastructureSystems({
        dynamicResponse: (req) => {
          if (req.query.search === "salesforce") {
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-searched.json",
            };
          }
          return {
            fixture:
              "detection-discovery/results/infrastructure-systems-with-data-uses.json",
          };
        },
      });

      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get("input[placeholder='Search']").type("salesforce");
      cy.wait("@getInfrastructureSystems");

      cy.url().should("include", "search=salesforce");
    });

    it("should trigger API call with search query parameter", () => {
      stubInfrastructureSystems({
        dynamicResponse: (req) => {
          if (req.query.search === "salesforce") {
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-searched.json",
            };
          }
          return {
            fixture:
              "detection-discovery/results/infrastructure-systems-with-data-uses.json",
          };
        },
      });

      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get("input[placeholder='Search']").type("salesforce");
      // the request is triggered twice when running the test but only the second
      // one has the search query param
      cy.wait("@getInfrastructureSystems");
      cy.wait("@getInfrastructureSystems").then((interception) => {
        expect(interception.request.query).to.have.property(
          "search",
          "salesforce",
        );
      });
    });

    describe("filter functionality", () => {
      beforeEach(() => {
        cy.login();
        stubPlus(true);
        stubTaxonomyEntities();
        stubInfrastructureSystemsFilters(monitorId);
      });

      it("should filter by status", () => {
        stubInfrastructureSystems({
          dynamicResponse: (req) => {
            if (req.query.diff_status === "muted") {
              return {
                fixture:
                  "detection-discovery/results/infrastructure-systems-filtered-by-status.json",
              };
            }
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-with-data-uses.json",
            };
          },
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.getByTestId("status-filter-select").click();
        cy.contains(".ant-select-item", "Ignored").click();
        cy.wait("@getInfrastructureSystems").then((interception) => {
          expect(interception.request.query).to.have.property("diff_status");
          expect(interception.request.query.diff_status).to.include("muted");
        });
      });

      it("should filter by data use", () => {
        stubInfrastructureSystems({
          dynamicResponse: (req) => {
            if (req.query.data_uses === "analytics") {
              return {
                fixture:
                  "detection-discovery/results/infrastructure-systems-filtered-by-data-use.json",
              };
            }
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-with-data-uses.json",
            };
          },
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");
        cy.wait("@getInfrastructureSystemsFilters");

        cy.getByTestId("data-use-filter-select").click();
        cy.contains(".ant-select-item", "Analytics").click();
        // Wait for both requests after filter change and find the one with correct params
        cy.wait("@getInfrastructureSystems");
        cy.wait("@getInfrastructureSystems");
        // Get all interceptions and find the one with data_uses param
        cy.get("@getInfrastructureSystems.all").then((interceptions) => {
          const interceptionsArray = interceptions as unknown as any[];
          // Find the interception with the data_uses query param
          const filteredInterception = interceptionsArray.find(
            (interception: any) =>
              interception.request.query?.data_uses?.includes("analytics"),
          );
          expect(filteredInterception).to.exist;
          expect(filteredInterception.request.query).to.have.property(
            "data_uses",
          );
          expect(filteredInterception.request.query.data_uses).to.include(
            "analytics",
          );
        });
      });

      it("should show reset filters button when filters are active", () => {
        stubInfrastructureSystems();

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.getByTestId("reset-filters-button").should("not.exist");

        cy.getByTestId("status-filter-select").click();
        cy.contains(".ant-select-item", "Ignored").click();
        cy.wait("@getInfrastructureSystems");

        cy.getByTestId("reset-filters-button").should("exist");
      });

      it("should reset all filters when reset button is clicked", () => {
        stubInfrastructureSystems({
          dynamicResponse: (req) => {
            if (
              !req.query.diff_status ||
              req.query.diff_status === "addition"
            ) {
              return {
                fixture:
                  "detection-discovery/results/infrastructure-systems-with-data-uses.json",
              };
            }
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-filtered-by-status.json",
            };
          },
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");
        cy.wait("@getInfrastructureSystemsFilters");

        cy.getByTestId("status-filter-select").click();
        cy.contains(".ant-select-item", "Ignored").click();
        cy.wait("@getInfrastructureSystems");

        cy.getByTestId("data-use-filter-select").click();
        cy.contains(".ant-select-item", "Analytics").click();
        cy.wait("@getInfrastructureSystems");

        cy.getByTestId("reset-filters-button").click();
        // Wait for both requests after reset button is clicked and find the one with correct params
        cy.wait("@getInfrastructureSystems");
        cy.wait("@getInfrastructureSystems").then((interception) => {
          expect(interception.request.query.diff_status).to.equal("addition");
          expect(interception.request.query.data_uses).to.be.undefined;
        });

        cy.getByTestId("reset-filters-button").should("not.exist");
      });
    });

    describe("selection functionality", () => {
      beforeEach(() => {
        cy.login();
        stubPlus(true);
        stubTaxonomyEntities();
        stubInfrastructureSystemsFilters(monitorId);
        stubInfrastructureSystems();
      });

      it("should select and deselect individual items", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("1 selected").should("exist");

        cy.get('input[type="checkbox"]').eq(1).uncheck();
        cy.contains("selected").should("not.exist");
      });

      it("should select all items on current page", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.contains("Select all").click();
        cy.contains("2 selected").should("exist");

        cy.contains("Select all").click();
        cy.contains("selected").should("not.exist");
      });

      it("should show indeterminate state when some items are selected", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.get('input[type="checkbox"]')
          .first()
          .should("have.prop", "indeterminate", true);
      });

      it("should show checked state when all items are selected", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.contains("Select all").click();
        cy.get('input[type="checkbox"]').first().should("be.checked");
      });

      it("should clear selection when filters change", () => {
        stubInfrastructureSystems({
          dynamicResponse: (req) => {
            if (req.query.diff_status === "muted") {
              return {
                fixture:
                  "detection-discovery/results/infrastructure-systems-filtered-by-status.json",
              };
            }
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-with-data-uses.json",
            };
          },
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("1 selected").should("exist");

        cy.getByTestId("status-filter-select").click();
        cy.contains(".ant-select-item", "Ignored").click();
        cy.wait("@getInfrastructureSystems");

        cy.contains("selected").should("not.exist");
      });

      it("should clear selection when search changes", () => {
        stubInfrastructureSystems({
          dynamicResponse: (req) => {
            if (req.query.search) {
              return {
                fixture:
                  "detection-discovery/results/infrastructure-systems-searched.json",
              };
            }
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-with-data-uses.json",
            };
          },
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("1 selected").should("exist");

        cy.get("input[placeholder='Search']").type("salesforce");
        cy.wait("@getInfrastructureSystems");

        cy.contains("selected").should("not.exist");
      });
    });

    describe("bulk actions", () => {
      beforeEach(() => {
        cy.login();
        stubPlus(true);
        stubTaxonomyEntities();
        stubInfrastructureSystemsFilters(monitorId);
        stubInfrastructureSystems();
        stubInfrastructureSystemsBulkActions(monitorId);
      });

      it("should disable bulk actions button when no items are selected", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.contains("button", "Actions").should("be.disabled");
      });

      it("should enable bulk actions button when items are selected", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("button", "Actions").should("not.be.disabled");
      });

      it("should show Add and Ignore actions on non-ignored tab", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("button", "Actions").click();

        cy.contains("Add").should("exist");
        cy.contains("Ignore").should("exist");
        cy.contains("Restore").should("not.exist");
      });

      it("should show Add and Restore actions when filtering for ignored systems", () => {
        stubInfrastructureSystems({
          fixture:
            "detection-discovery/results/infrastructure-systems-ignored-tab.json",
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.getByTestId("status-filter-select").click();
        cy.contains(".ant-select-item", "Ignored").click();
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("button", "Actions").click();

        cy.get(".ant-dropdown-menu-item").contains("Add").should("exist");
        cy.get(".ant-dropdown-menu-item").contains("Restore").should("exist");
        cy.get(".ant-dropdown-menu-item")
          .contains("Ignore")
          .should("not.exist");
      });

      it("should perform bulk Add action with explicit selection", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("button", "Actions").click();
        cy.contains("Add").click();

        cy.wait("@bulkPromoteInfrastructureSystems").then((interception) => {
          expect(interception.request.body).to.be.an("array");
          expect(interception.request.body).to.include(testUrn);
        });

        cy.getByTestId("toast-success-msg").should("contain", "promoted");
        cy.contains("selected").should("not.exist");
      });

      it("should perform bulk Ignore action with explicit selection", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("button", "Actions").click();
        cy.contains("Ignore").click();

        cy.wait("@bulkMuteInfrastructureSystems").then((interception) => {
          expect(interception.request.body).to.be.an("array");
          expect(interception.request.body).to.include(testUrn);
        });

        cy.getByTestId("toast-success-msg").should("contain", "ignored");
        cy.contains("selected").should("not.exist");
      });

      it("should perform bulk Restore action with explicit selection", () => {
        stubInfrastructureSystems({
          fixture:
            "detection-discovery/results/infrastructure-systems-ignored-tab.json",
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.getByTestId("status-filter-select").click();
        cy.contains(".ant-select-item", "Ignored").click();
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("button", "Actions").click();
        cy.contains("Restore").click();

        cy.wait("@bulkUnmuteInfrastructureSystems").then((interception) => {
          expect(interception.request.body).to.be.an("array");
          expect(interception.request.body).to.include(
            "urn:okta:app:ignored-1",
          );
        });

        cy.getByTestId("toast-success-msg").should("contain", "restored");
        cy.contains("selected").should("not.exist");
      });

      it("should perform bulk Add action with select all mode", () => {
        stubInfrastructureSystems({
          fixture:
            "detection-discovery/results/infrastructure-systems-large-dataset.json",
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.contains("Select all").click();
        cy.contains("button", "Actions").click();
        cy.contains("Add").click();

        cy.wait("@bulkPromoteInfrastructureSystems").then((interception) => {
          expect(interception.request.body).to.have.property("filters");
          expect(interception.request.body.filters).to.be.an("object");
        });

        cy.getByTestId("toast-success-msg").should("contain", "promoted");
      });

      it("should disable bulk actions during action in progress", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("button", "Actions").click();
        cy.contains("Add").click();

        cy.contains("button", "Actions").should("be.disabled");
      });

      it("should exclude items when using select all with exclusions", () => {
        stubInfrastructureSystems({
          fixture:
            "detection-discovery/results/infrastructure-systems-large-dataset.json",
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.contains("Select all").click();
        cy.get('input[type="checkbox"]').eq(1).uncheck();

        cy.contains("button", "Actions").click();
        cy.contains("Add").click();

        cy.wait("@bulkPromoteInfrastructureSystems").then((interception) => {
          expect(interception.request.body).to.have.property("exclude_urns");
          expect(interception.request.body.exclude_urns).to.be.an("array");
        });
      });
    });

    describe("integration scenarios", () => {
      beforeEach(() => {
        cy.login();
        stubPlus(true);
        stubTaxonomyEntities();
        stubInfrastructureSystemsFilters(monitorId);
      });

      it("should work with search, filter, and selection together", () => {
        stubInfrastructureSystems({
          dynamicResponse: (req) => {
            if (
              req.query.search === "salesforce" &&
              req.query.diff_status === "addition"
            ) {
              return {
                fixture:
                  "detection-discovery/results/infrastructure-systems-searched.json",
              };
            }
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-with-data-uses.json",
            };
          },
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get("input[placeholder='Search']").type("salesforce");
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("1 selected").should("exist");
      });

      it("should clear selection when filter changes", () => {
        stubInfrastructureSystems({
          dynamicResponse: (req) => {
            if (req.query.diff_status === "muted") {
              return {
                fixture:
                  "detection-discovery/results/infrastructure-systems-filtered-by-status.json",
              };
            }
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-with-data-uses.json",
            };
          },
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("1 selected").should("exist");

        cy.getByTestId("status-filter-select").click();
        cy.contains(".ant-select-item", "Ignored").click();
        cy.wait("@getInfrastructureSystems");

        cy.contains("selected").should("not.exist");
      });

      it("should clear selection when search changes", () => {
        stubInfrastructureSystems({
          dynamicResponse: (req) => {
            if (req.query.search) {
              return {
                fixture:
                  "detection-discovery/results/infrastructure-systems-searched.json",
              };
            }
            return {
              fixture:
                "detection-discovery/results/infrastructure-systems-with-data-uses.json",
            };
          },
        });

        cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
        cy.wait("@getInfrastructureSystems");

        cy.get('input[type="checkbox"]').eq(1).check();
        cy.contains("1 selected").should("exist");

        cy.get("input[placeholder='Search']").type("test");
        cy.wait("@getInfrastructureSystems");

        cy.contains("selected").should("not.exist");
      });
    });
  });
});
