// OneTrust Migration Integration Tests
// These tests verify the functionality of migrating OneTrust consent preferences to Fides

// Make TypeScript ignore window augmentation errors in test files
// @ts-ignore
export {};

describe("OneTrust to Fides consent migration", () => {
  const testOTMappingValue = encodeURIComponent(
    JSON.stringify({
      C0001: ["essential"],
      C0002: ["analytics"],
      C0004: ["advertising", "marketing"],
    }),
  );

  // Mock OneTrust cookie sample with various consent states
  const otConsentCookieAllAccepted =
    "OptanonConsent=isGpcEnabled=0&datestamp=Fri+Mar+07+2025+19%3A51%3A06+GMT%2B0100&version=202409.1.0&isIABGlobal=false&hosts=&consentId=f9c105b8-48e3-401a-87e9-363ad1f77531&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A1";
  const otConsentCookieMixed =
    "OptanonConsent=isGpcEnabled=0&datestamp=Fri+Mar+07+2025+19%3A51%3A06+GMT%2B0100&version=202409.1.0&isIABGlobal=false&hosts=&consentId=f9c105b8-48e3-401a-87e9-363ad1f77531&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A0";
  const otConsentCookieAllRejected =
    "OptanonConsent=isGpcEnabled=0&datestamp=Fri+Mar+07+2025+19%3A51%3A06+GMT%2B0100&version=202409.1.0&isIABGlobal=false&hosts=&consentId=f9c105b8-48e3-401a-87e9-363ad1f77531&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A0%2CC0002%3A0%2CC0004%3A0";

  beforeEach(() => {
    // Clear Fides cookie between tests
    cy.clearCookie("fides_consent");
  });

  describe("when user has OneTrust cookie but no Fides cookie", () => {
    it("should migrate consent from OneTrust (all accepted)", () => {
      // Set OneTrust cookie
      cy.setCookie("OptanonConsent", otConsentCookieAllAccepted);

      // Visit page with mapping config
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Wait for initialization
      cy.window().should("have.property", "Fides");
      cy.get("#consent-json").should("be.visible");

      // Verify Fides consent matches expected migration
      cy.get("#consent-json").should("contain", '"essential": true');
      cy.get("#consent-json").should("contain", '"analytics": true');
      cy.get("#consent-json").should("contain", '"advertising": true');
      cy.get("#consent-json").should("contain", '"marketing": true');

      // Verify OneTrust mapping was properly used
      cy.get("#consent-options").should("contain", "otFidesMapping");

      // Verify Fides cookie was created
      cy.getCookie("fides_consent").should("exist");
    });

    it("should migrate consent from OneTrust (mixed preferences)", () => {
      // Set OneTrust cookie with mixed preferences
      cy.setCookie("OptanonConsent", otConsentCookieMixed);

      // Visit page with mapping config
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Wait for initialization
      cy.window().should("have.property", "Fides");
      cy.get("#consent-json").should("be.visible");

      // Verify Fides consent matches expected migration (advertising and marketing should be false)
      cy.get("#consent-json").should("contain", '"essential": true');
      cy.get("#consent-json").should("contain", '"analytics": true');
      cy.get("#consent-json").should("contain", '"advertising": false');
      cy.get("#consent-json").should("contain", '"marketing": false');
    });

    it("should migrate consent from OneTrust (all rejected)", () => {
      // Set OneTrust cookie with all preferences rejected
      cy.setCookie("OptanonConsent", otConsentCookieAllRejected);

      // Visit page with mapping config
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Wait for initialization
      cy.window().should("have.property", "Fides");
      cy.get("#consent-json").should("be.visible");

      // Verify Fides consent matches expected migration (all should be false)
      cy.get("#consent-json").should("contain", '"essential": false');
      cy.get("#consent-json").should("contain", '"analytics": false');
      cy.get("#consent-json").should("contain", '"advertising": false');
      cy.get("#consent-json").should("contain", '"marketing": false');
    });
  });

  describe("OneTrust migration persistence", () => {
    it("should persist migrated consent in Fides cookie", () => {
      // Set OneTrust cookie
      cy.setCookie("OptanonConsent", otConsentCookieMixed);

      // First visit to migrate preferences
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Wait for initialization
      cy.window().should("have.property", "Fides");
      cy.get("#consent-json").should("be.visible");

      // Verify consent was migrated
      cy.get("#consent-json").should("contain", '"essential": true');
      cy.get("#consent-json").should("contain", '"analytics": true');
      cy.get("#consent-json").should("contain", '"advertising": false');

      // Clear the OneTrust cookie
      cy.clearCookie("OptanonConsent");

      // Reload the page
      cy.reload();

      // Verify the same consent values are still present
      cy.get("#consent-json").should("contain", '"essential": true');
      cy.get("#consent-json").should("contain", '"analytics": true');
      cy.get("#consent-json").should("contain", '"advertising": false');
    });
  });

  describe("Fides cookie precedence", () => {
    it("should prefer existing Fides cookie over OneTrust migration", () => {
      // First, create a Fides cookie with known preferences
      cy.visit("/fides-js-demo.html");

      // Wait for Fides to initialize
      cy.window().should("have.property", "Fides");
      cy.window().then((win) => {
        // @ts-ignore - Fides type is not important for test
        win.Fides.saveConsent({
          essential: true,
          analytics: false,
          advertising: true,
          marketing: false,
        });
      });

      // Then, set up OneTrust cookie (which should be ignored)
      cy.setCookie("OptanonConsent", otConsentCookieAllAccepted);

      // Reload page with mapping config
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Verify the Fides cookie preferences are used, not OneTrust
      cy.get("#consent-json").should("contain", '"essential": true');
      cy.get("#consent-json").should("contain", '"analytics": false');
      cy.get("#consent-json").should("contain", '"advertising": true');
      cy.get("#consent-json").should("contain", '"marketing": false');
    });
  });

  describe("Edge cases", () => {
    it("should handle empty or invalid OneTrust cookie", () => {
      // Set invalid OneTrust cookie
      cy.setCookie("OptanonConsent", "invalid&cookie&format");

      // Visit page with mapping config
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Fides should initialize with default preferences
      cy.window().should("have.property", "Fides");
      cy.get("#consent-json").should("be.visible");
    });

    it("should handle malformed mapping configuration", () => {
      // Set OneTrust cookie
      cy.setCookie("OptanonConsent", otConsentCookieAllAccepted);

      // Visit with invalid mapping
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: "not-valid-json",
          };
        },
      });

      // Fides should still initialize properly
      cy.window().should("have.property", "Fides");
      cy.get("#consent-json").should("be.visible");
    });

    it("should handle OneTrust categories that do not exist in mapping", () => {
      // Set OneTrust cookie with additional categories not in mapping
      cy.setCookie(
        "OptanonConsent",
        "OptanonConsent=groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0099%3A1",
      );

      // Visit page with mapping config (no C0003 or C0099 in mapping)
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Verify only mapped categories were migrated
      cy.window().should("have.property", "Fides");
      cy.get("#consent-json").should("be.visible");
      cy.get("#consent-json").should("contain", '"essential": true');
      cy.get("#consent-json").should("contain", '"analytics": true');
      // C0003 and C0099 should not affect any Fides notices
    });
  });

  describe("UI representation of migrated consent", () => {
    it("should show correct UI state in Fides consent modal for migrated preferences", () => {
      // Set OneTrust cookie with mixed preferences
      cy.setCookie("OptanonConsent", otConsentCookieMixed);

      // Visit page with mapping config
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Wait for initialization and open the consent modal
      cy.window().should("have.property", "Fides");
      cy.get("#fides-modal-link").click();

      // Wait for modal to appear
      cy.get(".fides-consent-control-container").should("be.visible");

      // Verify the toggle buttons match the migrated consent state
      // Note: The exact selector format may need adjustment based on your actual UI implementation
      cy.get(".fides-consent-control-container")
        .contains("Essential")
        .parent()
        .find('[role="switch"]')
        .should("have.attr", "aria-checked", "true");
      cy.get(".fides-consent-control-container")
        .contains("Analytics")
        .parent()
        .find('[role="switch"]')
        .should("have.attr", "aria-checked", "true");
      cy.get(".fides-consent-control-container")
        .contains("Advertising")
        .parent()
        .find('[role="switch"]')
        .should("have.attr", "aria-checked", "false");
      cy.get(".fides-consent-control-container")
        .contains("Marketing")
        .parent()
        .find('[role="switch"]')
        .should("have.attr", "aria-checked", "false");
    });

    it("should allow changing migrated preferences through the UI", () => {
      // Set OneTrust cookie with mixed preferences
      cy.setCookie("OptanonConsent", otConsentCookieMixed);

      // Visit page with mapping config
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Wait for initialization and open the consent modal
      cy.window().should("have.property", "Fides");
      cy.get("#fides-modal-link").click();

      // Toggle some preferences
      cy.get(".fides-consent-control-container")
        .contains("Analytics")
        .parent()
        .find('[role="switch"]')
        .click();
      cy.get(".fides-consent-control-container")
        .contains("Advertising")
        .parent()
        .find('[role="switch"]')
        .click();

      // Save preferences
      cy.get("button").contains("Save Preferences").click();

      // Verify the changes were saved
      cy.get("#consent-json").should("contain", '"analytics": false');
      cy.get("#consent-json").should("contain", '"advertising": true');

      // Verify original preferences are preserved
      cy.get("#consent-json").should("contain", '"essential": true');
      cy.get("#consent-json").should("contain", '"marketing": false');
    });

    it("should maintain consistent UI state after reloading with migrated preferences", () => {
      // Set OneTrust cookie
      cy.setCookie("OptanonConsent", otConsentCookieMixed);

      // First visit to migrate preferences
      cy.visit("/fides-js-demo.html", {
        onBeforeLoad: (win) => {
          // @ts-ignore - Window type is not important for test
          win.fides_overrides = {
            ot_fides_mapping: testOTMappingValue,
          };
        },
      });

      // Wait for initialization
      cy.window().should("have.property", "Fides");

      // Clear the OneTrust cookie and reload
      cy.clearCookie("OptanonConsent");
      cy.reload();

      // Open the consent modal
      cy.get("#fides-modal-link").click();

      // Verify UI state matches migrated preferences
      cy.get(".fides-consent-control-container")
        .contains("Essential")
        .parent()
        .find('[role="switch"]')
        .should("have.attr", "aria-checked", "true");
      cy.get(".fides-consent-control-container")
        .contains("Analytics")
        .parent()
        .find('[role="switch"]')
        .should("have.attr", "aria-checked", "true");
      cy.get(".fides-consent-control-container")
        .contains("Advertising")
        .parent()
        .find('[role="switch"]')
        .should("have.attr", "aria-checked", "false");
      cy.get(".fides-consent-control-container")
        .contains("Marketing")
        .parent()
        .find('[role="switch"]')
        .should("have.attr", "aria-checked", "false");
    });
  });
});
