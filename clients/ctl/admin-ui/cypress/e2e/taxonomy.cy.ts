describe("Taxonomy management page", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/data_category", {
      fixture: "data_categories.json",
    }).as("getDataCategories");
    cy.intercept("GET", "/api/v1/data_use", { fixture: "data_uses.json" }).as(
      "getDataUses"
    );
    cy.intercept("GET", "/api/v1/data_subject", {
      fixture: "data_subjects.json",
    }).as("getDataSubjects");
    cy.intercept("GET", "/api/v1/data_qualifier", {
      fixture: "data_qualifiers.json",
    }).as("getDataQualifiers");
  });

  it("Can navigate to the taxonomy page", () => {
    cy.visit("/");
    cy.getByTestId("nav-link-Taxonomy").click();
    cy.getByTestId("taxonomy-tabs");
    cy.getByTestId("tab-Data Categories");
    cy.getByTestId("tab-Data Uses");
    cy.getByTestId("tab-Data Subjects");
    cy.getByTestId("tab-Identifiability");
  });

  describe("Can view data", () => {
    beforeEach(() => {
      cy.visit("/taxonomy");
    });
    it("Can navigate between tabs and load data", () => {
      cy.getByTestId("tab-Data Uses").click();
      cy.wait("@getDataUses");
      cy.getByTestId("tab-Data Subjects").click();
      cy.wait("@getDataSubjects");
      cy.getByTestId("tab-Identifiability").click();
      cy.wait("@getDataQualifiers");
      cy.getByTestId("tab-Data Categories").click();
      cy.wait("@getDataCategories");
    });

    it("Can open up accordion to see taxonomy entities", () => {
      // should only see the 3 root level taxonomy
      cy.getByTestId("accordion-item-Account Data").should("be.visible");
      cy.getByTestId("accordion-item-System Data").should("be.visible");
      cy.getByTestId("accordion-item-User Data").should("be.visible");
      cy.getByTestId("accordion-item-Payment Data").should("not.be.visible");

      // clicking should open up accordions to render more items visible
      cy.getByTestId("accordion-item-Account Data").click();
      cy.getByTestId("accordion-item-Payment Data").should("be.visible");
      cy.getByTestId("accordion-item-Payment Data").click();
      cy.getByTestId("item-Account Payment Financial Account Number").should(
        "be.visible"
      );
    });

    it("Can render accordion elements on flat structures", () => {
      cy.getByTestId("tab-Data Subjects").click();
      cy.getByTestId("item-Anonymous User").should("be.visible");
      cy.getByTestId("item-Shareholder").should("be.visible");
    });

    it("Can render action buttons on hover", () => {
      cy.getByTestId("action-btns").should("not.exist");
      cy.getByTestId("accordion-item-Account Data").trigger("mouseover");
      cy.getByTestId("action-btns").should("exist");
    });
  });

  describe("Can edit data", () => {
    beforeEach(() => {
      cy.visit("/taxonomy");
      const taxonomyPayload = {
        statusCode: 200,
        body: {
          fides_key: "key",
          organization_fides_key: "default_organization",
          name: "name",
          description: "description",
          parent_key: "",
        },
      };
      cy.intercept("PUT", "/api/v1/data_category*", taxonomyPayload).as(
        "putDataCategory"
      );
      cy.intercept("PUT", "/api/v1/data_use*", taxonomyPayload).as(
        "putDataUse"
      );
      cy.intercept("PUT", "/api/v1/data_subject*", taxonomyPayload).as(
        "putDataSubject"
      );
      cy.intercept("PUT", "/api/v1/data_qualifier*", taxonomyPayload).as(
        "putDataQualifier"
      );
    });

    it("Can open an edit form for each taxonomy entity", () => {
      const expectedTabValues = [
        {
          tab: "Data Categories",
          name: "Account Data",
          key: "account",
          description: "Data related to a system account.",
          parentKey: "",
          isParent: true,
          request: "@putDataCategory",
        },
        {
          tab: "Data Uses",
          name: "Improve the capability",
          key: "improve",
          description: "Improve the product, service, application or system.",
          parentKey: "",
          isParent: true,
          request: "@putDataUse",
        },
        {
          tab: "Data Subjects",
          name: "Commuter",
          key: "commuter",
          description:
            "An individual that is traveling or transiting in the context of location tracking.",
          parentKey: "",
          isParent: false,
          request: "@putDataSubject",
        },
        {
          tab: "Identifiability",
          name: "Aggregated Data",
          key: "aggregated",
          description:
            "Statistical data that does not contain individually identifying information but includes information about groups of individuals that renders individual identification impossible.",
          parentKey: "",
          isParent: true,
          request: "@putDataQualifier",
        },
      ];
      expectedTabValues.forEach((tabValue) => {
        cy.getByTestId(`tab-${tabValue.tab}`).click();
        const testId = tabValue.isParent
          ? `accordion-item-${tabValue.name}`
          : `item-${tabValue.name}`;
        cy.getByTestId(testId).trigger("mouseover");
        cy.getByTestId("edit-taxonomy-form").should("not.exist");
        cy.getByTestId("edit-btn").click();
        cy.getByTestId("edit-taxonomy-form").should("exist");
        cy.getByTestId(`taxonomy-entity-${tabValue.key}`).should("exist");
        cy.getByTestId("input-name").should("have.value", tabValue.name);
        cy.getByTestId("input-description").should(
          "have.value",
          tabValue.description
        );
        cy.getByTestId("input-parent_key").should(
          "have.value",
          tabValue.parentKey
        );
        cy.getByTestId("input-parent_key").should("be.disabled");
        cy.getByTestId("update-btn").should("be.disabled");

        // make an edit
        const addedText = "foo";
        cy.getByTestId("input-name").type(addedText);
        cy.getByTestId("update-btn").should("be.enabled");
        cy.getByTestId("update-btn").click();
        cy.wait(tabValue.request).then((interception) => {
          const { body } = interception.request;
          expect(body.name).to.eql(`${tabValue.name}${addedText}`);
        });
        cy.getByTestId("toast-success-msg").should("exist");
      });
    });

    it("Can render the parent field", () => {
      cy.getByTestId("tab-Data Categories").click();
      cy.getByTestId(`accordion-item-Account Data`).click();
      cy.getByTestId("accordion-item-Payment Data").click();
      cy.getByTestId("item-Account Payment Financial Account Number").trigger(
        "mouseover"
      );
      cy.getByTestId("edit-btn").click();
      cy.getByTestId("input-parent_key").should(
        "have.value",
        "account.payment"
      );
    });

    it("Can trigger an error", () => {
      const errorMsg = "Internal Server Error";
      cy.intercept("PUT", "/api/v1/data_category*", {
        statusCode: 500,
        body: errorMsg,
      }).as("putDataCategoryError");
      // cy.visit("/taxonomy")
      cy.getByTestId(`tab-Data Categories`).click();
      cy.getByTestId("accordion-item-Account Data").trigger("mouseover");
      cy.getByTestId("edit-btn").click();

      const addedText = "foo";
      cy.getByTestId("input-name").type(addedText);
      cy.getByTestId("update-btn").click();

      cy.wait("@putDataCategoryError");
      cy.getByTestId("toast-success-msg").should("not.exist");
      cy.getByTestId("taxonomy-form-error").should("contain", errorMsg);
    });
  });
});
