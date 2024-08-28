import { stubPlus } from "cypress/support/stubs";

const getSelectOptionList = (selectorId: string) =>
  cy.getByTestId(selectorId).click().find(`.custom-select__menu-list`);

describe("Messaging", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);

    cy.intercept("/api/v1/plus/messaging/templates/summary?*", {
      fixture: "messaging/summary.json",
    }).as("getEmailTemplatesSummary");

    cy.intercept("/api/v1/messaging/templates/default/*", {
      fixture: "messaging/default.json",
    }).as("getTemplateDefaultTexts");

    cy.intercept("GET", "/api/v1/plus/properties*", {
      fixture: "properties/properties.json",
    }).as("getProperties");

    cy.intercept("PATCH", "/api/v1/plus/messaging/templates/*", {}).as(
      "patchTemplate",
    );

    cy.intercept(
      "POST",
      "/api/v1/plus/messaging/templates/privacy_request_complete_access",
      {},
    ).as("postTemplate");
  });

  it("should display the messaging page results", () => {
    cy.visit("/messaging");
    cy.wait("@getEmailTemplatesSummary");

    cy.get("table").find("tbody").find("tr").should("have.length", 10);
  });

  it("should display a notice when a property doesn't have any messaging templates", () => {
    cy.visit("/messaging");
    cy.wait("@getEmailTemplatesSummary");

    cy.getByTestId("notice-properties-without-messaging-templates").should(
      "be.visible",
    );
  });

  it("should allow toggle of the email template status", () => {
    cy.visit("/messaging");
    cy.wait("@getEmailTemplatesSummary");

    cy.get("table")
      .find("tbody")
      .find("tr")
      .first()
      .find("td input")
      .uncheck({ force: true });

    cy.wait("@patchTemplate").then((interception) => {
      expect(interception.request.body).to.deep.equal({
        is_enabled: false,
      });
      expect(interception.request.url).to.contain(
        "autogenerated-mes_26e6fb9d-3b4a-4313-87b9-2bed3c0be185",
      );
    });
  });

  it("should display message type selector after clicking on the add button", () => {
    const customizableMessagesCount = 6;

    cy.visit("/messaging");
    cy.wait("@getEmailTemplatesSummary");

    cy.getByTestId("add-message-btn").click();

    cy.getByTestId("add-messaging-template-modal").should("exist");

    getSelectOptionList("template-type-selector")
      .find(".custom-select__option")
      .should("have.length", customizableMessagesCount);
  });

  it("should redirect to the add new page after selecting a message type", () => {
    cy.visit("/messaging");
    cy.wait("@getEmailTemplatesSummary");

    cy.getByTestId("add-message-btn").click();

    cy.selectOption("template-type-selector", "Access request completed");

    cy.getByTestId("confirm-btn").click();

    cy.url().should(
      "contain",
      "/messaging/add-template?templateType=privacy_request_complete_access",
    );
  });

  it("load default when adding new message", () => {
    cy.visit(
      "/messaging/add-template?templateType=privacy_request_complete_access",
    );

    cy.wait("@getTemplateDefaultTexts");

    cy.getByTestId("input-content.subject").should(
      "have.value",
      "Your data is ready to be downloaded",
    );
    cy.getByTestId("input-content.body").should(
      "have.value",
      "Your access request has been completed and can be downloaded at {{download_link}}. For security purposes, this secret link will expire in {{days}} days.",
    );

    cy.getByTestId("input-is_enabled").find("input").should("not.be.checked");
  });

  it("should save template after selecting a property and clicking save", () => {
    cy.visit(
      "/messaging/add-template?templateType=privacy_request_complete_access",
    );

    cy.wait("@getTemplateDefaultTexts");
    cy.wait("@getProperties");

    cy.getByTestId("submit-btn").should("be.disabled");
    cy.getByTestId("add-property").click();
    cy.getByTestId("select-property")
      .find(".select-property__input-container")
      .click();
    cy.getByTestId("select-property").find("input").focus().type("{enter}");
    cy.getByTestId("submit-btn").should("be.enabled");
    cy.getByTestId("submit-btn").click();

    cy.wait("@postTemplate").then((interception) => {
      expect(interception.request.body).to.deep.equal({
        is_enabled: false,
        content: {
          subject: "Your data is ready to be downloaded",
          body: "Your access request has been completed and can be downloaded at {{download_link}}. For security purposes, this secret link will expire in {{days}} days.",
        },
        properties: ["FDS-CEA9EV"],
      });
    });
  });
});
