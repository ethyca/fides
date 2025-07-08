import { API_URL } from "../support/constants";

describe("Privacy Request with custom fields with query params", () => {
  beforeEach(() => {
    cy.intercept("POST", `${API_URL}/privacy-request`, {
      fixture: "privacy-request/success",
    }).as("postPrivacyRequest");
  });

  it("displays a visible custom field, prefilled with the value from query param", () => {
    cy.visit("/?name=John");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_custom_request_fields.json").then(
      () => {
        cy.getByTestId("card").contains("Access your data").click();
        cy.getByTestId("privacy-request-form")
          .find("#name")
          .should("be.visible")
          .and("have.value", "John");
      },
    );
  });

  it("send hidden custom field as part of the request with the value from query param", () => {
    cy.visit("/?name=John&my_custom_app_id=123");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_custom_request_fields.json").then(
      () => {
        cy.getByTestId("card").contains("Access your data").click();

        cy.getByTestId("privacy-request-form")
          .find("#email")
          .type("test@test.com");

        cy.getByTestId("privacy-request-form")
          .find("button[type='submit']")
          .click();

        cy.wait("@postPrivacyRequest").then((interception) => {
          const customPrivacyRequestFields =
            interception.request.body[0].custom_privacy_request_fields;
          expect(customPrivacyRequestFields.my_custom_app_id.value).to.equal(
            "123",
          );
        });
      },
    );
  });

  it("uses default value if query param doesn't have a value", () => {
    cy.visit("/?name=John");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_custom_request_fields.json").then(
      () => {
        cy.getByTestId("card").contains("Access your data").click();

        cy.getByTestId("privacy-request-form")
          .find("#email")
          .type("test@test.com");

        cy.getByTestId("privacy-request-form")
          .find("button[type='submit']")
          .click();

        cy.wait("@postPrivacyRequest").then((interception) => {
          const customPrivacyRequestFields =
            interception.request.body[0].custom_privacy_request_fields;
          expect(
            customPrivacyRequestFields.another_custom_app_id.value,
          ).to.equal("12345");
        });
      },
    );
  });
});

describe("Privacy Request with multiselect custom fields", () => {
  beforeEach(() => {
    cy.intercept("POST", `${API_URL}/privacy-request`, {
      fixture: "privacy-request/success",
    }).as("postPrivacyRequest");
  });

  it("displays multiselect fields with default values", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.getByTestId("card").contains("Erase your data").click();

    // Check that the data_categories multiselect field is displayed
    cy.getByTestId("privacy-request-form").within(() => {
      // Verify data_categories multiselect field is displayed
      cy.get('[data-testid="select-data_categories"]').should("be.visible");

      // Verify regular email field is present
      cy.get("#email").should("be.visible");
    });
  });

  it("allows selecting and deselecting options in multiselect fields", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.getByTestId("card").contains("Erase your data").click();

    cy.getByTestId("privacy-request-form").within(() => {
      // Select multiple data categories by typing
      cy.get('[data-testid="select-data_categories"]').click();
      cy.get('[data-testid="select-data_categories"]').type(
        "Profile Information{enter}",
      );
      cy.get('[data-testid="select-data_categories"]').type(
        "Analytics Data{enter}",
      );

      // Verify selections were added
      cy.get('[data-testid="select-data_categories"]').within(() => {
        cy.get(
          '.ant-select-selection-item[title="Profile Information"]',
        ).should("exist");
        cy.get('.ant-select-selection-item[title="Analytics Data"]').should(
          "exist",
        );
      });

      // Remove one selection by clicking its close button
      cy.get('[data-testid="select-data_categories"]')
        .find(
          '.ant-select-selection-item[title="Profile Information"] .ant-select-selection-item-remove',
        )
        .click();

      // Verify one was removed but the other remains
      cy.get('[data-testid="select-data_categories"]').within(() => {
        cy.get('.ant-select-selection-item[title="Analytics Data"]').should(
          "exist",
        );
        cy.get(
          '.ant-select-selection-item[title="Profile Information"]',
        ).should("not.exist");
      });
    });
  });

  it("sends multiselect values correctly to backend API", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.getByTestId("card").contains("Erase your data").click();

    cy.getByTestId("privacy-request-form").within(() => {
      // Fill required email
      cy.get("#email").type("test@test.com");

      // Select multiple data categories by typing
      cy.get('[data-testid="select-data_categories"]').click();
      cy.get('[data-testid="select-data_categories"]').type(
        "Profile Information{enter}",
      );
      cy.get('[data-testid="select-data_categories"]').type(
        "User Preferences{enter}",
      );
      cy.get('[data-testid="select-data_categories"]').type(
        "Analytics Data{enter}",
      );

      // Close the dropdown by clicking on another field to avoid covering the submit button
      cy.get("#email").click();

      // Submit form
      cy.get("button[type='submit']").click();

      // Verify the request payload
      cy.wait("@postPrivacyRequest").then((interception) => {
        const customPrivacyRequestFields =
          interception.request.body[0].custom_privacy_request_fields;

        // Verify data_categories array contains selected values
        expect(customPrivacyRequestFields.data_categories.value).to.deep.equal([
          "Profile Information",
          "User Preferences",
          "Analytics Data",
        ]);

        // Verify field has proper label
        expect(customPrivacyRequestFields.data_categories.label).to.equal(
          "Select data categories to erase",
        );
      });
    });
  });

  it("handles empty multiselect fields correctly", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.getByTestId("card").contains("Erase your data").click();

    cy.getByTestId("privacy-request-form").within(() => {
      // Fill required email
      cy.get("#email").type("test@test.com");

      // Don't select any data categories (it's optional)
      // Submit form with empty multiselect
      cy.get("button[type='submit']").click();

      // Verify empty array is sent correctly
      cy.wait("@postPrivacyRequest").then((interception) => {
        const customPrivacyRequestFields =
          interception.request.body[0].custom_privacy_request_fields;

        // Empty multiselect field should send empty array or undefined
        const dataCategories =
          customPrivacyRequestFields.data_categories?.value;
        expect(dataCategories).to.satisfy(
          (val: any) =>
            val === undefined || (Array.isArray(val) && val.length === 0),
        );
      });
    });
  });

  it("works correctly with erasure policy form", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.getByTestId("card").contains("Erase your data").click();

    cy.getByTestId("privacy-request-form").within(() => {
      // Verify data_categories multiselect is available in erasure form
      cy.get('[data-testid="select-data_categories"]').should("be.visible");

      // Fill required email
      cy.get("#email").type("test@test.com");

      // Select data category by typing
      cy.get('[data-testid="select-data_categories"]').click();
      cy.get('[data-testid="select-data_categories"]').type(
        "Activity History{enter}",
      );

      // Close the dropdown by clicking on another field to avoid covering the submit button
      cy.get("#email").click();

      // Submit form
      cy.get("button[type='submit']").click();

      // Verify the request payload for erasure
      cy.wait("@postPrivacyRequest").then((interception) => {
        const customPrivacyRequestFields =
          interception.request.body[0].custom_privacy_request_fields;

        expect(customPrivacyRequestFields.data_categories.value).to.deep.equal([
          "Activity History",
        ]);
        expect(customPrivacyRequestFields.data_categories.label).to.equal(
          "Select data categories to erase",
        );
      });
    });
  });

  it("displays and works with select fields correctly", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.getByTestId("card").contains("Access your data").click();

    cy.getByTestId("privacy-request-form").within(() => {
      // Verify preferred_format select field is displayed
      cy.get('[data-testid="select-preferred_format"]').should("be.visible");

      // Fill required email
      cy.get("#email").type("test@test.com");

      // Select preferred format by typing
      cy.get('[data-testid="select-preferred_format"]').click();
      cy.get('[data-testid="select-preferred_format"]').type("HTML{enter}");

      // Verify selection was made
      cy.get('[data-testid="select-preferred_format"]').within(() => {
        cy.get('.ant-select-selection-item[title="HTML"]').should("exist");
      });

      // Close the dropdown by clicking on another field to avoid covering the submit button
      cy.get("#email").click();

      // Submit form
      cy.get("button[type='submit']").click();

      // Verify the request payload
      cy.wait("@postPrivacyRequest").then((interception) => {
        const customPrivacyRequestFields =
          interception.request.body[0].custom_privacy_request_fields;

        // Verify preferred_format field contains selected value as string
        expect(customPrivacyRequestFields.preferred_format.value).to.equal(
          "HTML",
        );
        expect(customPrivacyRequestFields.preferred_format.label).to.equal(
          "Preferred format",
        );
      });
    });
  });
});
