describe("Connectors", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/connection*", {
      fixture: "connectors/list.json",
    }).as("getConnectors");
    cy.intercept("GET", "/api/v1/connection_type*", {
      fixture: "connectors/connection_types.json",
    }).as("getConnectionTypes");
  });
  describe("Configuring connectors", () => {
    beforeEach(() => {
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
        },
      ).as("getPostgresConnectorDatasetconfig");

      cy.intercept("POST", "/api/v1/dataset/upsert", { body: {} }).as(
        "upsertDataset",
      );
      cy.intercept(
        "PATCH",
        "/api/v1/connection/postgres_connector/datasetconfig",
        { body: {} },
      ).as("patchDatasetconfig");
      cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
        "getDatasets",
      );
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

    it("Should allow saving a dataset configuration via dropdown", () => {
      cy.visit("/datastore-connection");
      cy.getByTestId("connection-grid-item-postgres_connector").within(() => {
        cy.getByTestId("connection-menu-btn").click();
      });
      cy.getByTestId("connection-menu-postgres_connector").within(() => {
        cy.getByTestId("configure-btn").click();
      });
      cy.getByTestId("tab-Dataset configuration").click();
      cy.wait("@getPostgresConnectorDatasetconfig");

      // The yaml editor will start off disabled
      cy.getByTestId("save-yaml-btn").should("be.disabled");
      // The dataset dropdown selector should have the value of the existing connected dataset
      cy.getByTestId("save-dataset-link-btn").should("be.enabled");
      cy.getByTestId("dataset-selector").should(
        "have.text",
        "postgres_example_test_dataset",
      );

      // Change the linked dataset
      cy.getByTestId("dataset-selector").antSelect("demo_users_dataset_2");

      cy.getByTestId("save-dataset-link-btn").click();

      cy.wait("@patchDatasetconfig").then((interception) => {
        expect(interception.request.body).to.eql([
          {
            fides_key: "postgres_example_test_dataset",
            ctl_dataset_fides_key: "demo_users_dataset_2",
          },
        ]);
      });
    });

    it("Should allow saving a dataset configuration via yaml", () => {
      cy.visit("/datastore-connection");
      cy.getByTestId("connection-grid-item-postgres_connector").within(() => {
        cy.getByTestId("connection-menu-btn").click();
      });
      cy.getByTestId("connection-menu-postgres_connector").within(() => {
        cy.getByTestId("configure-btn").click();
      });
      cy.getByTestId("tab-Dataset configuration").click();
      cy.wait("@getPostgresConnectorDatasetconfig");

      // Unset the linked dataset, which should switch the save button enable-ness
      cy.getByTestId("dataset-selector").antClearSelect();
      cy.getByTestId("save-dataset-link-btn").should("be.disabled");
      // The monaco yaml editor takes a bit to load
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(1000);
      cy.getByTestId("save-yaml-btn").click();

      // Click past the confirmation modal
      cy.getByTestId("confirmation-modal");
      cy.getByTestId("continue-btn").click();

      cy.wait("@upsertDataset").then((interception) => {
        expect(interception.request.body.length).to.eql(1);
        expect(interception.request.body[0].fides_key).to.eql(
          "postgres_example_test_dataset",
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

    it("Should not show the dataset selector if no datasets exist", () => {
      cy.intercept("GET", "/api/v1/dataset", { body: [] }).as("getDatasets");
      cy.intercept(
        "GET",
        "/api/v1/connection/postgres_connector/datasetconfig",
        {
          body: {
            items: [],
          },
        },
      ).as("getEmptyPostgresConnectorDatasetconfig");

      cy.visit("/datastore-connection");
      cy.getByTestId("connection-grid-item-postgres_connector").within(() => {
        cy.getByTestId("connection-menu-btn").click();
      });
      cy.getByTestId("connection-menu-postgres_connector").within(() => {
        cy.getByTestId("configure-btn").click();
      });
      cy.getByTestId("tab-Dataset configuration").click();
      cy.wait("@getEmptyPostgresConnectorDatasetconfig");
      cy.getByTestId("dataset-selector-section").should("not.exist");
    });
  });

  describe("Email connector", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/connection_type/sovrn/secret", {
        fixture: "connectors/sovrn_secret.json",
      }).as("getSovrnSecret");
      cy.intercept("PATCH", "/api/v1/connection", {
        fixture: "connectors/patch_connection.json",
      }).as("patchSovrn");
      cy.intercept("PUT", "/api/v1/connection/sovrn-test/secret*", {
        fixture: "connectors/put_secret.json",
      }).as("putSovrnSecret");
    });

    it("allows the user to add an email connector", () => {
      cy.visit("/datastore-connection/new");
      cy.getByTestId("connection-type-filter").antSelect("Email connectors");
      cy.getByTestId("sovrn-item").click();
      cy.url().should("contain", "/new?step=2");

      // fill out the form
      const identifier = "sovrn-test";
      const recipientEmailAddress = "sovrn-test";
      cy.get("input").get(`[name='name']`).type(identifier);
      cy.get("input").get(`[name='instance_key']`).type(identifier);
      cy.get("input")
        .get(`[name='recipient_email_address']`)
        .type(recipientEmailAddress);
      cy.get("button").contains("Save").click();
      cy.wait("@patchSovrn").then((interception) => {
        const { body } = interception.request;
        expect(body).to.eql([
          {
            access: "write",
            connection_type: "sovrn",
            description: "",
            disabled: false,
            key: identifier,
            name: identifier,
          },
        ]);
      });
      cy.wait("@putSovrnSecret").then((interception) => {
        const { body } = interception.request;
        expect(body).to.eql({
          third_party_vendor_name: "Sovrn",
          recipient_email_address: recipientEmailAddress,
          test_email_address: null,
          advanced_settings: null,
        });
      });
    });
  });
});
