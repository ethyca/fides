import {
  ADMIN_UI_URL,
  API_URL,
  PRIVACY_CENTER_URL,
  SAMPLE_APP_URL,
} from "support/constants";

describe("Smoke test", () => {
  it("can submit an access request from the Privacy Center", () => {
    // Watch these routes without changing or stubbing its response
    cy.intercept("PATCH", `${API_URL}/privacy-request/administrate/approve`).as(
      "patchRequest"
    );
    cy.intercept("GET", `${API_URL}/privacy-request*`).as("getRequests");
    cy.intercept("POST", `${API_URL}/privacy-request`).as("postPrivacyRequest");

    // Submit the access request from the privacy center
    cy.visit(PRIVACY_CENTER_URL);
    cy.getByTestId("card").contains("Access your data").click();
    cy.getByTestId("privacy-request-form").within(() => {
      cy.get("input#email").type("jenny@example.com");
      cy.get("input#first_name").type("Jenny");
      cy.get("input#color").clear().type("blue");
      cy.get("button").contains("Continue").click();
    });

    // Verify the privacy request payload
    cy.wait("@postPrivacyRequest").then((interception) => {
      expect(interception.request.body).to.deep.equal([
        {
          identity: {
            email: "jenny@example.com",
            phone_number: "",
          },
          custom_privacy_request_fields: {
            first_name: {
              label: "First name",
              value: "Jenny",
            },
            last_name: {
              label: "Last name",
              value: "",
            },
            color: {
              label: "Color",
              value: "blue",
            },
            tenant_id: {
              label: "Tenant ID",
              value: "123",
            },
          },
          policy_key: "default_access_policy",
        },
      ]);
    });

    // Approve the request in the admin UI
    cy.visit(ADMIN_UI_URL);
    cy.origin(ADMIN_UI_URL, () => {
      // Makes custom commands available to all subsequent cy.origin() commands
      // https://docs.cypress.io/api/commands/origin#Custom-commands
      Cypress.require("support/commands");
      cy.login();
      cy.get("div").contains("Review privacy requests").click();
      let numCompletedRequests = 0;
      let mostRecentPrivacyRequestId: string;
      cy.wait("@getRequests").then((interception) => {
        const { items } = interception.response.body;
        numCompletedRequests = items.filter(
          (i) => i.status === "complete"
        ).length;
        mostRecentPrivacyRequestId = Cypress._.maxBy(items, "created_at").id;
      });

      cy.getByTestId("privacy-request-row-pending")
        .first()
        .trigger("mouseover")
        .get("button")
        .contains("Approve")
        .click();

      // Go past the confirmation modal
      cy.getByTestId("continue-btn").click();

      cy.wait("@patchRequest");
      cy.wait("@getRequests");

      // Make sure there is one more completed request than originally
      cy.getByTestId("privacy-request-row-complete").then((rows) => {
        expect(rows.length).to.eql(numCompletedRequests + 1);
        cy.readFile(`../../fides_uploads/${mostRecentPrivacyRequestId}.zip`);
      });
    });
  });

  it("can access Mongo and Postgres connectors from the Admin UI", () => {
    cy.visit(ADMIN_UI_URL);
    cy.login();

    // Postgres
    cy.getByTestId("Systems & vendors-nav-link").click();
    cy.getByTestId("system-cookie_house_postgresql_database").click();
    cy.getByTestId("tab-Integrations").click();
    cy.get("button").contains("Test").click();

    // Mongo
    cy.getByTestId("Systems & vendors-nav-link").click();
    cy.getByTestId("system-cookie_house_customer_database").click();
    cy.getByTestId("tab-Integrations").click();
    cy.get("button").contains("Test").click();
  });

  it("can manage consent preferences from the Privacy Center", () => {
    cy.visit(PRIVACY_CENTER_URL);
    cy.getCookie("fides_consent").should("not.exist");
    cy.getByTestId("card").contains("Manage your consent").click();
    cy.getByTestId("consent-request-form").within(() => {
      cy.get("input#email").type("jenny@example.com");
      cy.get("input#first_name").type("Jenny");
      cy.get("input#color").clear().type("blue");
      cy.get("button").contains("Continue").click();
    });

    // Check the defaults for Cookie House are what we expect:
    //  - Data Sales or Sharing => true
    //  - Email Marketing => true
    //  - Product Analytics => true
    cy.getByTestId(`consent-item-marketing.advertising`).within(() => {
      cy.contains("Data Sales or Sharing");
      cy.getRadio("true").should("be.checked");
      cy.getRadio("false").should("not.be.checked");
    });
    cy.getByTestId(`consent-item-marketing.advertising.first_party`).within(
      () => {
        cy.contains("Email Marketing");
        cy.getRadio("true").should("be.checked");
        cy.getRadio("false").should("not.be.checked");
      }
    );
    cy.getByTestId(`consent-item-functional`).within(() => {
      cy.contains("Product Analytics");
      cy.getRadio("true").should("be.checked");
      cy.getRadio("false").should("not.be.checked");
    });

    // Opt-out of data sales / sharing
    cy.getByTestId(`consent-item-marketing.advertising`).within(() => {
      cy.getRadio("false").check({ force: true });
    });
    cy.contains("Save").click();
    cy.contains("Your consent preferences have been saved");

    // Reload and confirm preferences were saved
    cy.visit(PRIVACY_CENTER_URL);
    cy.reload();
    cy.getByTestId("card").contains("Manage your consent").click();
    cy.getByTestId("consent-request-form").within(() => {
      cy.get("input#email").type("jenny@example.com");
      cy.get("input#first_name").type("Jenny");
      cy.get("input#color").clear().type("blue");
      cy.get("button").contains("Continue").click();
    });
    cy.getByTestId(`consent-item-marketing.advertising`).within(() => {
      cy.getRadio("true").should("not.be.checked");
      cy.getRadio("false").should("be.checked");
    });
    cy.getCookie("fides_consent").should("exist");

    // Visit the Cookie House sample app and confirm saved consent preferences are loaded
    cy.visit(SAMPLE_APP_URL);
    cy.origin(SAMPLE_APP_URL, () => {
      cy.getCookie("fides_consent").should("exist");
      cy.window().then((win) => {
        cy.wrap(win).should("to.have.property", "Fides");
        cy.wrap(win)
          .should("to.have.nested.property", "Fides.fides_meta.version")
          .should("eql", "0.9.0");
        cy.wrap(win)
          .should("to.have.nested.property", "Fides.consent")
          .should("eql", {
            data_sales: false,
            tracking: true,
            analytics: true,
          });
        cy.wrap(win).should(
          "to.have.nested.property",
          "Fides.identity.fides_user_device_id"
        );
      });
    });
  });
});
