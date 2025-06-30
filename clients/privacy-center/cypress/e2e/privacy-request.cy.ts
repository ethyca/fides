import { API_URL } from "../support/constants";

describe("Privacy request", () => {
  describe("when requesting data access", () => {
    beforeEach(() => {
      cy.intercept("POST", `${API_URL}/privacy-request`, {
        fixture: "privacy-request/unverified",
      }).as("postPrivacyRequest");
      cy.intercept(
        "POST",
        `${API_URL}/privacy-request/privacy-request-id/verify`,
        { body: {} },
      ).as("postPrivacyRequestVerify");
    });

    it("requires valid inputs", () => {
      cy.visit("/");
      cy.loadConfigFixture("config/config_all.json").then(() => {
        cy.getByTestId("card").contains("Access your data").click();

        cy.getByTestId("privacy-request-form").within(() => {
          // This block uses `.root()` to keep queries within the form. This is necessary because of
          // `.blur()` which triggers input validation.

          // test email being typed, continue becoming disabled due to invalid email
          cy.root().get("input#email").type("invalid email").blur();
          cy.root().should("contain", "Email is invalid");
          cy.root().get("button").contains("Continue").should("be.disabled");
          cy.root().get("input#email").clear().blur();

          // test valid email, continue becoming enabled due to valid email
          cy.root().get("input#email").type("valid@example.com").blur();
          cy.root().get("button").contains("Continue").should("be.enabled");
          cy.root().get("input#email").clear().blur();
        });
      });
    });
  });
});

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
    cy.loadConfigFixture("config/config_multiselect_fields.json").then(() => {
      cy.getByTestId("card").contains("Access your data").click();

      // Check that multiselect fields are displayed
      cy.getByTestId("privacy-request-form").within(() => {
        // Verify departments field shows with default value
        cy.get('[data-testid="select-departments"]')
          .should("be.visible")
          .within(() => {
            // Check that Engineering (default value) is selected
            cy.get('.ant-select-selection-item[title="Engineering"]').should(
              "exist",
            );
          });

        // Verify regions field shows with multiple default values
        cy.get('[data-testid="select-regions"]')
          .should("be.visible")
          .within(() => {
            cy.get('.ant-select-selection-item[title="North America"]').should(
              "exist",
            );
            cy.get('.ant-select-selection-item[title="Europe"]').should(
              "exist",
            );
          });

        // Verify required multiselect field is displayed
        cy.get('[data-testid="select-interests"]').should("be.visible");

        // Verify regular text field still works
        cy.get("#regular_text_field")
          .scrollIntoView()
          .should("be.visible")
          .and("have.value", "test default");
      });
    });
  });

  it("allows selecting and deselecting options in multiselect fields", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_multiselect_fields.json").then(() => {
      cy.getByTestId("card").contains("Access your data").click();

      cy.getByTestId("privacy-request-form").within(() => {
        // Open departments dropdown and add Marketing
        cy.get('[data-testid="select-departments"]').click();
        cy.get(".privacy-form-dropdown").should("be.visible");
        cy.get('.privacy-form-dropdown .ant-select-item[title="Marketing"]')
          .should("be.visible")
          .click();

        // Verify Marketing was added
        cy.get('[data-testid="select-departments"]').within(() => {
          cy.get('.ant-select-selection-item[title="Marketing"]').should(
            "exist",
          );
          cy.get('.ant-select-selection-item[title="Engineering"]').should(
            "exist",
          );
        });

        // Remove Engineering by clicking its close button
        cy.get('[data-testid="select-departments"]')
          .find(
            '.ant-select-selection-item[title="Engineering"] .ant-select-selection-item-remove',
          )
          .click();

        // Verify Engineering was removed but Marketing remains
        cy.get('[data-testid="select-departments"]').within(() => {
          cy.get('.ant-select-selection-item[title="Marketing"]').should(
            "exist",
          );
          cy.get('.ant-select-selection-item[title="Engineering"]').should(
            "not.exist",
          );
        });
      });
    });
  });

  it("validates required multiselect fields", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_multiselect_fields.json").then(() => {
      cy.getByTestId("card").contains("Access your data").click();

      cy.getByTestId("privacy-request-form").within(() => {
        // Fill email (required)
        cy.get("#email").type("test@test.com");

        // Try to submit without selecting required interests field
        cy.get("button[type='submit']").click();

        // Should show validation error
        cy.should("contain", "Areas of Interest is required");
        cy.get("button[type='submit']").should("be.disabled");

        // Add a selection to interests field
        cy.get('[data-testid="select-interests"]').click();
        cy.get(".privacy-form-dropdown").should("be.visible");
        cy.get('.privacy-form-dropdown .ant-select-item[title="Privacy"]')
          .should("be.visible")
          .click();

        // Form should now be valid
        cy.get("button[type='submit']").should("be.enabled");
      });
    });
  });

  it("sends multiselect values correctly to backend API", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_multiselect_fields.json").then(() => {
      cy.getByTestId("card").contains("Access your data").click();

      cy.getByTestId("privacy-request-form").within(() => {
        // Fill required email
        cy.get("#email").type("test@test.com");

        // Select multiple values in departments (modify default)
        cy.get('[data-testid="select-departments"]').click();
        cy.get(".privacy-form-dropdown").should("be.visible");
        cy.get('.privacy-form-dropdown .ant-select-item[title="Marketing"]')
          .should("be.visible")
          .click();
        cy.get('.privacy-form-dropdown .ant-select-item[title="Sales"]')
          .should("be.visible")
          .click();
        // Close dropdown by clicking outside
        cy.get("body").click();

        // Select required interests
        cy.get('[data-testid="select-interests"]').click();
        cy.get(".privacy-form-dropdown").should("be.visible");
        cy.get('.privacy-form-dropdown .ant-select-item[title="Privacy"]')
          .should("be.visible")
          .click();
        cy.get('.privacy-form-dropdown .ant-select-item[title="Security"]')
          .should("be.visible")
          .click();
        // Close dropdown by clicking outside
        cy.get("body").click();

        // Modify regions (add one, remove one)
        cy.get('[data-testid="select-regions"]').click();
        cy.get(".privacy-form-dropdown").should("be.visible");
        cy.get('.privacy-form-dropdown .ant-select-item[title="Asia"]')
          .should("be.visible")
          .click();
        // Close dropdown by clicking outside
        cy.get("body").click();
        // Remove Europe
        cy.get('[data-testid="select-regions"]')
          .find(
            '.ant-select-selection-item[title="Europe"] .ant-select-selection-item-remove',
          )
          .click();

        // Submit form
        cy.get("button[type='submit']").click();

        // Verify the request payload
        cy.wait("@postPrivacyRequest").then((interception) => {
          const customPrivacyRequestFields =
            interception.request.body[0].custom_privacy_request_fields;

          // Verify departments array contains Engineering (default), Marketing, Sales
          expect(customPrivacyRequestFields.departments.value).to.deep.equal([
            "Engineering",
            "Marketing",
            "Sales",
          ]);

          // Verify interests array contains selected values
          expect(customPrivacyRequestFields.interests.value).to.deep.equal([
            "Privacy",
            "Security",
          ]);

          // Verify regions array contains North America and Asia (Europe removed)
          expect(customPrivacyRequestFields.regions.value).to.deep.equal([
            "North America",
            "Asia",
          ]);

          // Verify regular text field is sent as string
          expect(customPrivacyRequestFields.regular_text_field.value).to.equal(
            "test default",
          );

          // Verify hidden multiselect is sent with default values
          expect(
            customPrivacyRequestFields.hidden_multiselect.value,
          ).to.deep.equal(["Option1", "Option2"]);

          // Verify all fields have proper labels
          expect(customPrivacyRequestFields.departments.label).to.equal(
            "Departments",
          );
          expect(customPrivacyRequestFields.interests.label).to.equal(
            "Areas of Interest",
          );
          expect(customPrivacyRequestFields.regions.label).to.equal(
            "Geographic Regions",
          );
        });
      });
    });
  });

  it("handles empty multiselect fields correctly", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_multiselect_fields.json").then(() => {
      cy.getByTestId("card").contains("Access your data").click();

      cy.getByTestId("privacy-request-form").within(() => {
        // Fill required email
        cy.get("#email").type("test@test.com");

        // Clear all default values from departments
        cy.get('[data-testid="select-departments"]')
          .find(
            '.ant-select-selection-item[title="Engineering"] .ant-select-selection-item-remove',
          )
          .click();

        // Clear all default values from regions
        cy.get('[data-testid="select-regions"]')
          .find(
            '.ant-select-selection-item[title="North America"] .ant-select-selection-item-remove',
          )
          .click();
        cy.get('[data-testid="select-regions"]')
          .find(
            '.ant-select-selection-item[title="Europe"] .ant-select-selection-item-remove',
          )
          .click();

        // Add required interests selection
        cy.get('[data-testid="select-interests"]').click();
        cy.get(".privacy-form-dropdown").should("be.visible");
        cy.get('.privacy-form-dropdown .ant-select-item[title="Technology"]')
          .should("be.visible")
          .click();

        // Submit form
        cy.get("button[type='submit']").click();

        // Verify empty arrays are sent correctly
        cy.wait("@postPrivacyRequest").then((interception) => {
          const customPrivacyRequestFields =
            interception.request.body[0].custom_privacy_request_fields;

          // Empty multiselect fields should send empty arrays
          expect(customPrivacyRequestFields.departments.value).to.deep.equal(
            [],
          );
          expect(customPrivacyRequestFields.regions.value).to.deep.equal([]);

          // Required field should have selection
          expect(customPrivacyRequestFields.interests.value).to.deep.equal([
            "Technology",
          ]);
        });
      });
    });
  });

  it("works correctly with erasure policy form", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_multiselect_fields.json").then(() => {
      cy.getByTestId("card").contains("Erase your data").click();

      cy.getByTestId("privacy-request-form").within(() => {
        // Verify departments multiselect is available in erasure form
        cy.get('[data-testid="select-departments"]').should("be.visible");

        // Fill required email
        cy.get("#email").type("test@test.com");

        // Select department
        cy.get('[data-testid="select-departments"]').click();
        cy.get(".privacy-form-dropdown").should("be.visible");
        cy.get('.privacy-form-dropdown .ant-select-item[title="HR"]')
          .should("be.visible")
          .click();

        // Submit form
        cy.get("button[type='submit']").click();

        // Verify the request payload for erasure
        cy.wait("@postPrivacyRequest").then((interception) => {
          const customPrivacyRequestFields =
            interception.request.body[0].custom_privacy_request_fields;

          expect(customPrivacyRequestFields.departments.value).to.deep.equal([
            "HR",
          ]);
          expect(customPrivacyRequestFields.departments.label).to.equal(
            "Departments",
          );
        });
      });
    });
  });
});

describe("Consent Request with multiselect custom fields", () => {
  beforeEach(() => {
    cy.intercept("POST", `${API_URL}/consent-request`, {
      body: { consent_request_id: "test-consent-request-id" },
    }).as("postConsentRequest");
  });

  it("sends multiselect values correctly in consent request", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_multiselect_fields.json").then(() => {
      cy.getByTestId("card").contains("Manage your consent").click();

      cy.getByTestId("consent-request-form").within(() => {
        // Fill required email
        cy.get("#email").type("test@test.com");

        // Verify consent categories multiselect is displayed with default
        cy.get('[data-testid="select-consent_categories"]')
          .should("be.visible")
          .within(() => {
            cy.get('.ant-select-selection-item[title="Essential"]').should(
              "exist",
            );
          });

        // Add additional consent categories
        cy.get('[data-testid="select-consent_categories"]').click();
        cy.get(".privacy-form-dropdown").should("be.visible");
        cy.get('.privacy-form-dropdown .ant-select-item[title="Analytics"]')
          .should("be.visible")
          .click();
        cy.get('.privacy-form-dropdown .ant-select-item[title="Functional"]')
          .should("be.visible")
          .click();
        // Close dropdown by clicking outside
        cy.get("body").click();

        // Submit form
        cy.get("button[type='submit']").click();

        // Verify the consent request payload
        cy.wait("@postConsentRequest").then((interception) => {
          const customPrivacyRequestFields =
            interception.request.body.custom_privacy_request_fields;

          expect(
            customPrivacyRequestFields.consent_categories.value,
          ).to.deep.equal(["Essential", "Analytics", "Functional"]);
          expect(customPrivacyRequestFields.consent_categories.label).to.equal(
            "Consent Categories",
          );
        });
      });
    });
  });
});
