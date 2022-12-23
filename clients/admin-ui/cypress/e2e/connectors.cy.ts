describe("Connectors", () => {
  beforeEach(() => {
    cy.login();
  });
  describe("Configuring connectors", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/connection*", {
        fixture: "connectors/list.json",
      }).as("getConnectors");
      cy.intercept("GET", "/api/v1/connection_type*", {
        fixture: "connectors/connection_types.json",
      }).as("getConnectionTypes");
      cy.intercept("GET", "/api/v1/connection/postgres_connector", {
        fixture: "connectors/postgres_connector.json",
      }).as("getPostgresConnector");
      cy.intercept("GET", "/api/v1/connection_type/postgres/secret", {
        fixture: "connectors/postgres_secret.json",
      }).as("getPostgresConnectorSecret");
      cy.intercept(
        "GET",
        "/api/v1/connection/postgres_connector/datasetconfig",
        {
          fixture: "connectors/datasetconfig.json",
        }
      ).as("getPostgresConnectorDatasetconfig");

      cy.intercept("POST", "/api/v1/dataset/upsert", { body: {} }).as(
        "upsertDataset"
      );
      cy.intercept(
        "PATCH",
        "/api/v1/connection/postgres_connector/datasetconfig",
        { body: {} }
      ).as("patchDatasetconfig");
    });

    it("Should show data store connections and view configuration", () => {
      cy.visit("/datastore-connection");
      cy.getByTestId("connection-grid-item-mongodb_connector");
      cy.getByTestId("connection-grid-item-postgres_connector").within(() => {
        cy.getByTestId("connection-menu-btn").click();
      });
      cy.getByTestId("connection-menu-postgres_connector").within(() => {
        cy.getByTestId("configure-btn").click();
      });
      cy.getByTestId("input-name").should("have.value", "postgres_connector");
    });

    it("Should allow saving a dataset configuration", () => {
      cy.visit("/datastore-connection/postgres_connector");
      cy.getByTestId("tab-Dataset configuration").click();
      cy.wait("@getPostgresConnectorDatasetconfig");
      // The monaco yaml editor takes a bit to load. Since this is likely going away,
      // just wait for now and remove this once the yaml editor is no longer available
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(1000);
      cy.getByTestId("save-btn").click();
      cy.wait("@upsertDataset").then((interception) => {
        expect(interception.request.body.length).to.eql(1);
        expect(interception.request.body[0].fides_key).to.eql(
          "postgres_example_test_dataset"
        );
      });
      cy.wait("@patchDatasetconfig").then((interception) => {
        expect(interception.request.body).to.eql([
          {
            fides_key: "postgres_example_test_dataset",
            ctl_dataset_fides_key: "postgres_example_test_dataset",
          },
        ]);
      });
    });
  });
});
