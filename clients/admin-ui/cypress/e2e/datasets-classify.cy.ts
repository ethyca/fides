import {
  CONNECTION_STRING,
  stubDatasetCrud,
  stubPlus,
} from "cypress/support/stubs";

import { ClassificationResponse, ClassificationStatus } from "~/types/api";

/**
 * This test suite is a parallel of datasets.cy.ts for testing Dataset features when the user has
 * access to the  Fidescls API. This suite should cover the behavior that is different when a
 * dataset is classified.
 */

describe("Datasets with Fides Classify", () => {
  beforeEach(() => {
    cy.login();
  });

  beforeEach(() => {
    stubDatasetCrud();
    stubPlus(true);
    cy.intercept("GET", "/api/v1/plus/classify?resource_type=datasets", {
      fixture: "classify/list.json",
    }).as("getClassifyList");
    cy.visit("/dataset/new");
    cy.wait("@getPlusHealth");
  });

  describe.skip("Creating datasets", () => {
    // workflow will be deprecated soon, disabled now with d&d
    it("Shows the classify switch", () => {
      cy.getByTestId("connect-db-btn").click();

      cy.getByTestId("input-classify").find("input").should("be.checked");
      cy.getByTestId("input-classify").click();
      cy.getByTestId("input-classify").find("input").should("not.be.checked");
    });

    it("Can render the 'Status' column and classification status badges in the dataset table when plus features are enabled", () => {
      cy.visit("/dataset");
      cy.wait("@getFilteredDatasets");
      cy.getByTestId("dataset-table");
      cy.getByTestId("row-3");

      cy.getByTestId("dataset-table__status-table-header").should(
        "have.text",
        "Status",
      );
      cy.getByTestId("classification-status-badge").should("not.exist");
    });

    it("Classifies the dataset after generating it", () => {
      // Fill out the form.
      cy.getByTestId("connect-db-btn").click();
      cy.getByTestId("input-url").type(CONNECTION_STRING);
      cy.getByTestId("create-dataset-btn").click();

      // A modal opens to confirm the classify request.
      cy.getByTestId("confirmation-modal");

      // Confirmation will kick off the chain of API calls.
      cy.intercept("POST", "/api/v1/generate", {
        fixture: "generate/dataset.json",
      }).as("postGenerate");
      cy.intercept("POST", "/api/v1/plus/classify", {
        fixture: "classify/create.json",
      }).as("postClassify");

      // Confirm the request.
      cy.getByTestId("confirmation-modal").getByTestId("continue-btn").click();

      cy.wait("@postGenerate");
      cy.wait("@postDataset");
      cy.wait("@postClassify").then((interception) => {
        expect(
          interception.request.body.schema_config.generate.config
            .connection_string,
        ).to.eql(CONNECTION_STRING);
        expect(interception.request.body.dataset_schemas).to.eql([
          { fides_key: "public", name: "public" },
        ]);
      });

      // The dataset query should be re-fetched.
      cy.wait("@getFilteredDatasets");

      cy.url().should("match", /dataset$/);

      // The combination of Next routing and a toast message makes Cypress get weird
      // when re-running this test case. Introducing a delay fixes it.
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(100);
      cy.getByTestId("toast-success-msg");
    });
  });

  describe("Dataset collection view", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/dataset/*", {
        fixture: "classify/dataset-in-review.json",
      }).as("getDataset");
      cy.intercept("GET", "/api/v1/plus/classify/details/*", {
        fixture: "classify/get-in-review.json",
      }).as("getClassify");
    });

    /**
     * This helper checks that a row displays the relevant values. It finds appropriate elements by
     * testid, but tests by matching the displayed text - e.g. "Identified" instead of the whole
     * data_qualifier.
     */
    const rowContains = ({
      name,
      taxonomyEntities,
    }: {
      name: string;
      identifiability: string;
      taxonomyEntities: string[];
    }) => {
      cy.getByTestId(`field-row-${name}`).within(() => {
        taxonomyEntities.forEach((te) => {
          cy.getByTestIdPrefix("taxonomy-entity").contains(te);
        });
      });
    };

    it("Shows the classifiers field suggestions", () => {
      cy.visit("/dataset/dataset_in_review");
      cy.wait("@getDataset");
      cy.wait("@getClassify");

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
        taxonomyEntities: ["user.device"],
      });
      // The classifier thinks this is an address, but it's been overwritten.
      rowContains({
        name: "state",
        identifiability: "Unlinked Pseudonymized",
        taxonomyEntities: ["system.operations"],
      });
    });
  });

  describe("Approve classification button", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/dataset/*", {
        fixture: "classify/dataset-in-review.json",
      }).as("getDataset");
      cy.intercept("GET", "/api/v1/plus/classify/details/*", {
        fixture: "classify/get-in-review.json",
      }).as("getClassify");

      cy.intercept("PUT", "/api/v1/dataset/*", {
        fixture: "classify/dataset-in-review.json",
      }).as("putDataset");
      cy.intercept("PUT", "/api/v1/plus/classify?resource_type=datasets", {
        fixture: "classify/update.json",
      }).as("putClassify");
    });

    it("Updates blank fields with top classifications", () => {
      cy.visit("/dataset/dataset_in_review");
      cy.wait("@getDataset");
      cy.wait("@getClassify");

      // The button triggers a chain of requests that will modify the classify list response.
      cy.fixture("classify/get-in-review.json").then(
        (draftInstance: ClassificationResponse) => {
          draftInstance.datasets[0].status = ClassificationStatus.REVIEWED;

          cy.intercept("GET", "/api/v1/plus/classify/details/*", {
            body: draftInstance,
          }).as("getClassify");
        },
      );

      cy.getByTestId("approve-classification-btn").should("be.enabled").click();

      // The mutation should run.
      cy.wait("@putDataset");
      cy.getByTestId("toast-success-msg");
    });
  });

  describe("Data category input", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/dataset/*", {
        fixture: "classify/dataset-in-review.json",
      }).as("getDataset");
      cy.intercept("GET", "/api/v1/plus/classify/details/*", {
        fixture: "classify/get-in-review.json",
      }).as("getClassify");
    });

    it("Allows selection of suggested and non-suggested categories", () => {
      cy.visit("/dataset/dataset_in_review");
      cy.wait("@getDataset");
      cy.wait("@getClassify");

      // Open the "device" field editor.
      cy.getByTestId("field-row-device").click();

      // The plain list of categories should be replaced with the classified selector.
      cy.getByTestId("selected-categories").should("not.exist");

      // The highest-scoring category should be shown.
      cy.getByTestId("classified-select").contains("user.device");

      // Select a suggested category from the dropdown.
      cy.getByTestId("classified-select").click("right");
      cy.get("[data-testid=classified-select] [role=option]")
        .contains("user.contact.phone_number")
        .click();

      // Select a category from the taxonomy.
      cy.getByTestId("data-category-dropdown").click();
      cy.getByTestId("data-category-checkbox-tree")
        .contains("Location Data")
        .click();
      cy.getByTestId("data-category-done-btn").click();

      // Both selected categories should be rendered.
      cy.getByTestId("classified-select").contains("user.contact.phone_number");
      cy.getByTestId("classified-select").contains("user.location");

      // Both selected categories should be submitted on the dataset.
      cy.getByTestId("save-btn");
      cy.getByTestId("save-btn").click();
      cy.wait("@putDataset").then((interception) => {
        const { body } = interception.request;
        expect(body.collections[0].fields[1].data_categories).to.eql([
          "user.device",
          "user.contact.phone_number",
          "user.location",
        ]);
      });
    });
  });
});
