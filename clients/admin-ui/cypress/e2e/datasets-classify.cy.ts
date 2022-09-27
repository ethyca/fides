/**
 * This test suite is a parallel of datasets.cy.ts for testing Dataset features when the user has
 * access to the  Fidescls API. This suite should cover the behavior that is different when a
 * dataset is classified.
 */
describe("Datasets with Fides Classify", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/plus/health", {
      statusCode: 200,
      body: {
        status: "healthy",
        core_fidesctl_version: "1.8",
      },
    }).as("getPlusHealth");
  });

  describe("Creating datasets", () => {
    it("Shows the classify switch", () => {
      cy.visit("/dataset/new");
      cy.getByTestId("connect-db-btn").click();

      cy.getByTestId("input-classify").find("input").should("be.checked");
      cy.getByTestId("input-classify").click();
      cy.getByTestId("input-classify").find("input").should("not.be.checked");
    });

    it("Classifies the dataset after generating it", () => {
      // Fill out the form.
      cy.visit("/dataset/new");
      cy.getByTestId("connect-db-btn").click();
      cy.getByTestId("input-url").type(
        "postgresql://postgres:fidesctl@fidesctl-db:5432/fidesctl_test"
      );
      cy.getByTestId("create-dataset-btn").click();

      // A modal opens to confirm the classify request.
      cy.getByTestId("confirmation-modal");

      // Confirmation will kick off the chain of API calls.
      cy.intercept("POST", "/api/v1/generate", {
        fixture: "generate/dataset.json",
      }).as("postGenerate");
      cy.intercept("POST", "/api/v1/dataset", { fixture: "dataset.json" }).as(
        "postDataset"
      );
<<<<<<< HEAD:clients/admin-ui/cypress/e2e/datasets-classify.cy.ts
      cy.intercept("POST", "/api/v1/plus/classification", {
        fixture: "classification/create.json",
      }).as("postClassification");
=======
      cy.intercept("POST", "/api/v1/plus/classify", {
        fixture: "classify/create.json",
      }).as("postClassify");
>>>>>>> unified-fides-2:clients/ctl/admin-ui/cypress/e2e/datasets-classify.cy.ts
      cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
        "getDatasets"
      );

      // Confirm the request.
      cy.getByTestId("confirmation-modal").getByTestId("continue-btn").click();

      cy.wait("@postGenerate");
      cy.wait("@postDataset");
<<<<<<< HEAD:clients/admin-ui/cypress/e2e/datasets-classify.cy.ts
      cy.wait("@postClassification");
=======
      cy.wait("@postClassify");
>>>>>>> unified-fides-2:clients/ctl/admin-ui/cypress/e2e/datasets-classify.cy.ts
      cy.wait("@getDatasets");

      cy.url().should("match", /dataset$/);

      // The combination of Next routing and a toast message makes Cypress get weird
      // when re-running this test case. Introducing a delay fixes it.
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(100);
      cy.getByTestId("toast-success-msg");
    });
  });

  describe("List of datasets with classifications", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
        "getDatasets"
      );
<<<<<<< HEAD:clients/admin-ui/cypress/e2e/datasets-classify.cy.ts
      cy.intercept("GET", "/api/v1/plus/classification", {
        fixture: "classification/list.json",
      }).as("getClassificationList");
    });

    it("Shows the each dataset's classification status", () => {
      cy.visit("/dataset");
      cy.wait("@getDatasets");
      cy.wait("@getClassificationList");
=======
      cy.intercept("GET", "/api/v1/plus/classify", {
        fixture: "classify/list.json",
      }).as("getClassifyList");
    });

    it("Shows the each dataset's classify status", () => {
      cy.visit("/dataset");
      cy.wait("@getDatasets");
      cy.wait("@getClassifyList");
>>>>>>> unified-fides-2:clients/ctl/admin-ui/cypress/e2e/datasets-classify.cy.ts
      cy.getByTestId("dataset-table");
      cy.getByTestId("dataset-status-demo_users_dataset").contains("Unknown");
      cy.getByTestId("dataset-status-demo_users_dataset_2").contains(
        "Processing"
      );
      cy.getByTestId("dataset-status-demo_users_dataset_3").contains(
        "Awaiting Review"
      );
      cy.getByTestId("dataset-status-demo_users_dataset_4").contains(
        "Classified"
      );
    });
  });
<<<<<<< HEAD:clients/admin-ui/cypress/e2e/datasets-classify.cy.ts
=======

  describe("Dataset collection view", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/dataset/*", {
        fixture: "classify/dataset-in-review.json",
      }).as("getDataset");
      cy.intercept("GET", "/api/v1/data_category", {
        fixture: "data_categories.json",
      }).as("getDataCategory");

      cy.intercept("GET", "/api/v1/plus/classify", {
        fixture: "classify/list.json",
      }).as("getClassifyList");
    });

    /**
     * This helper checks that a row displays the relevant values. It finds appropriate elements by
     * testid, but tests by matching the displayed text - e.g. "Identified" instead of the whole
     * data_qualifier.
     */
    const rowContains = ({
      name,
      identifiability,
      taxonomyEntities,
    }: {
      name: string;
      identifiability: string;
      taxonomyEntities: string[];
    }) => {
      cy.getByTestId(`field-row-${name}`).within(() => {
        cy.get(`[data-testid^=identifiability-tag-]`).contains(identifiability);
        taxonomyEntities.forEach((te) => {
          // Right now this displays the whole taxonomy path, but this might be abbreviated later.
          cy.get(`[data-testid^=taxonomy-entity-]`).contains(te);
        });
      });
    };

    it("Shows the classifiers field suggestions", () => {
      cy.visit("/dataset/dataset_in_review");
      cy.wait("@getDataset");
      cy.wait("@getClassifyList");

      cy.getByTestId("dataset-fields-table");

      rowContains({
        name: "email",
        identifiability: "Identified",
        taxonomyEntities: ["user.email"],
      });
      // A row with multiple classifier suggestions.
      rowContains({
        name: "device",
        identifiability: "Pseudonymized",
        taxonomyEntities: ["user.device", "user.contact.phone_number"],
      });
      // The classifier thinks this is an address, but it's been overwritten.
      rowContains({
        name: "state",
        identifiability: "Unlinked Pseudonymized",
        taxonomyEntities: ["system.operations"],
      });
    });
  });
>>>>>>> unified-fides-2:clients/ctl/admin-ui/cypress/e2e/datasets-classify.cy.ts
});
