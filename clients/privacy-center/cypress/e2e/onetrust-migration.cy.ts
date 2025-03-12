// OneTrust Migration Integration Tests
// These tests verify the functionality of migrating OneTrust consent preferences to Fides

// Make TypeScript ignore window augmentation errors in test files

import { CONSENT_COOKIE_NAME, ConsentMethod, FidesCookie } from "fides-js";

import { stubConfig } from "~/cypress/support/stubs";

export {};

const ADVERTISING_KEY = "advertising";
const ESSENTIAL_KEY = "essential";
const ANALYTICS_KEY = "analytics_opt_out";

const testOTMappingValue = encodeURIComponent(
  JSON.stringify({
    C0001: ["essential"], // to test that essential cannot be opted-out
    C0002: ["analytics_opt_out"],
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

describe("OneTrust to Fides consent migration", () => {
  beforeEach(() => {
    // Clear Fides cookie between tests
    cy.clearCookie("fides_consent");
    // Clear OT cookie between tests
    cy.clearCookie("OptanonConsent");
  });

  describe("when user has OneTrust cookie but no Fides cookie", () => {
    it("should migrate consent from OneTrust (all accepted)", () => {
      // Set OneTrust cookie
      cy.setCookie("OptanonConsent", otConsentCookieAllAccepted);

      const overrides = {
        ot_fides_mapping: testOTMappingValue,
      };
      // Stub the experience with the following defaults:
      // analytics: true, advertising: false, essential: true
      cy.fixture("consent/experience_banner_modal.json").then((experience) => {
        stubConfig(
          {
            experience: experience.items[0],
          },
          null,
          null,
          undefined,
          { ...overrides },
        );
      });

      cy.waitUntilFidesInitialized().then(() => {
        // Banner should not exist since all notices have consents
        cy.get("div#fides-banner").should("not.exist");

        cy.get("#fides-modal-link").click();

        // Verify Fides UI matches expected migration
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });

        cy.getByTestId("Save-btn").click();
        // Modal should close after saving
        cy.getByTestId("consent-modal").should("not.be.visible");

        // Verify Fides cookie was created
        cy.getCookie("fides_consent").should("exist");
        // check that the cookie updated
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            expect(cookieKeyConsent.consent)
              .property(ADVERTISING_KEY)
              .is.eql(true);
            expect(cookieKeyConsent.consent)
              .property(ESSENTIAL_KEY)
              .is.eql(true);
            expect(cookieKeyConsent.consent)
              .property(ANALYTICS_KEY)
              .is.eql(true);
            expect(cookieKeyConsent.fides_meta)
              .property("consentMethod")
              .is.eql(ConsentMethod.SAVE);
          });
        });

        // check that window.Fides.consent updated
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [ADVERTISING_KEY]: true,
            [ESSENTIAL_KEY]: true,
            [ANALYTICS_KEY]: true,
          });
      });
    });
  });

  it("should migrate consent from OneTrust (mixed preferences)", () => {
    // Set OneTrust cookie with mixed preferences
    cy.setCookie("OptanonConsent", otConsentCookieMixed);

    const overrides = {
      ot_fides_mapping: testOTMappingValue,
    };
    // Stub the experience with the following defaults:
    // analytics: true, advertising: false, essential: true
    cy.fixture("consent/experience_banner_modal.json").then((experience) => {
      stubConfig(
        {
          experience: experience.items[0],
        },
        null,
        null,
        undefined,
        { ...overrides },
      );
    });

    cy.waitUntilFidesInitialized().then(() => {
      // Banner should not exist since all notices have consents
      cy.get("div#fides-banner").should("not.exist");

      cy.get("#fides-modal-link").click();

      // Verify Fides UI matches expected migration
      cy.getByTestId("toggle-Advertising").within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId("toggle-Analytics").within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId("toggle-Essential").within(() => {
        cy.get("input").should("be.checked");
      });

      cy.getByTestId("Save-btn").click();
      // Modal should close after saving
      cy.getByTestId("consent-modal").should("not.be.visible");

      // Verify Fides cookie was created
      cy.getCookie("fides_consent").should("exist");
      // check that the cookie updated
      cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value),
          );
          expect(cookieKeyConsent.consent)
            .property(ADVERTISING_KEY)
            .is.eql(false);
          expect(cookieKeyConsent.consent).property(ESSENTIAL_KEY).is.eql(true);
          expect(cookieKeyConsent.consent).property(ANALYTICS_KEY).is.eql(true);
          expect(cookieKeyConsent.fides_meta)
            .property("consentMethod")
            .is.eql(ConsentMethod.SAVE);
        });
      });

      // check that window.Fides.consent updated
      cy.window()
        .its("Fides")
        .its("consent")
        .should("eql", {
          [ADVERTISING_KEY]: false,
          [ESSENTIAL_KEY]: true,
          [ANALYTICS_KEY]: true,
        });
    });
  });

  it("should migrate consent from OneTrust (all rejected)", () => {
    // Set OneTrust cookie with all preferences rejected
    cy.setCookie("OptanonConsent", otConsentCookieAllRejected);

    const overrides = {
      ot_fides_mapping: testOTMappingValue,
    };
    // Stub the experience with the following defaults:
    // analytics: true, advertising: false, essential: true
    cy.fixture("consent/experience_banner_modal.json").then((experience) => {
      stubConfig(
        {
          experience: experience.items[0],
        },
        null,
        null,
        undefined,
        { ...overrides },
      );
    });

    cy.waitUntilFidesInitialized().then(() => {
      // Banner should not exist since all notices have consents
      cy.get("div#fides-banner").should("not.exist");

      cy.get("#fides-modal-link").click();

      // Verify Fides UI matches expected migration
      cy.getByTestId("toggle-Advertising").within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId("toggle-Analytics").within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId("toggle-Essential").within(() => {
        cy.get("input").should("be.checked");
      });

      cy.getByTestId("Save-btn").click();
      // Modal should close after saving
      cy.getByTestId("consent-modal").should("not.be.visible");

      // Verify Fides cookie was created
      cy.getCookie("fides_consent").should("exist");
      // check that the cookie updated
      cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value),
          );
          expect(cookieKeyConsent.consent)
            .property(ADVERTISING_KEY)
            .is.eql(false);
          expect(cookieKeyConsent.consent).property(ESSENTIAL_KEY).is.eql(true);
          expect(cookieKeyConsent.consent)
            .property(ANALYTICS_KEY)
            .is.eql(false);
          expect(cookieKeyConsent.fides_meta)
            .property("consentMethod")
            .is.eql(ConsentMethod.SAVE);
        });
      });

      // check that window.Fides.consent updated
      cy.window()
        .its("Fides")
        .its("consent")
        .should("eql", {
          [ADVERTISING_KEY]: false,
          [ESSENTIAL_KEY]: true,
          [ANALYTICS_KEY]: false,
        });
    });
  });
});

describe("OneTrust migration persistence", () => {
  it("should persist migrated consent in Fides cookie", () => {
    // Set OneTrust cookie
    cy.setCookie("OptanonConsent", otConsentCookieMixed);

    const overrides = {
      ot_fides_mapping: testOTMappingValue,
    };
    // Stub the experience with the following defaults:
    // analytics: true, advertising: false, essential: true
    cy.fixture("consent/experience_banner_modal.json").then((experience) => {
      stubConfig(
        {
          experience: experience.items[0],
        },
        null,
        null,
        undefined,
        { ...overrides },
      );
    });

    cy.waitUntilFidesInitialized().then(() => {
      // Banner should not exist since all notices have consents
      cy.get("div#fides-banner").should("not.exist");

      cy.get("#fides-modal-link").click();

      // Verify Fides UI matches expected migration
      cy.getByTestId("toggle-Advertising").within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId("toggle-Analytics").within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId("toggle-Essential").within(() => {
        cy.get("input").should("be.checked");
      });

      cy.getByTestId("Save-btn").click();
      // Modal should close after saving
      cy.getByTestId("consent-modal").should("not.be.visible");

      // Clear the OneTrust cookie
      cy.clearCookie("OptanonConsent");

      // Reload the page but now we shouldn't need to pass in any OT override info
      cy.fixture("consent/experience_banner_modal.json").then((experience) => {
        stubConfig({
          experience: experience.items[0],
        });
      });

      cy.get("#fides-modal-link").click();

      // Verify Fides UI matches expected migration
      cy.getByTestId("toggle-Advertising").within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId("toggle-Analytics").within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId("toggle-Essential").within(() => {
        cy.get("input").should("be.checked");
      });
    });
  });
});

describe("Fides cookie precedence", () => {
  it("should prefer existing Fides cookie over OneTrust migration", () => {
    // Set OneTrust cookie
    cy.setCookie("OptanonConsent", otConsentCookieAllAccepted);

    // Set Fides cookie
    const uuid = "4fbb6edf-34f6-4717-a6f1-52o47rybwuafh5";
    const CREATED_DATE = "2022-12-24T12:00:00.000Z";
    const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
    const notices = {
      // we skip setting the "applied" notice key since we wish to replicate no user pref here
      analytics_opt_out: false,
      advertising: false,
      essential: true,
    };
    const originalCookie = {
      identity: { fides_user_device_id: uuid },
      fides_meta: {
        version: "0.9.0",
        createdAt: CREATED_DATE,
        updatedAt: UPDATED_DATE,
      },
      consent: notices,
    };
    cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

    const overrides = {
      ot_fides_mapping: testOTMappingValue,
    };
    // Stub the experience with the following defaults:
    // analytics: true, advertising: false, essential: true
    cy.fixture("consent/experience_banner_modal.json").then((experience) => {
      stubConfig(
        {
          experience: experience.items[0],
        },
        null,
        null,
        undefined,
        { ...overrides },
      );
    });

    cy.waitUntilFidesInitialized().then(() => {
      // Banner should not exist since all notices have consents
      cy.get("div#fides-banner").should("not.exist");

      cy.get("#fides-modal-link").click();

      // Verify Fides UI matches cookie values
      cy.getByTestId("toggle-Advertising").within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId("toggle-Analytics").within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId("toggle-Essential").within(() => {
        cy.get("input").should("be.checked");
      });
    });
  });

  describe("Edge cases", () => {
    it("should handle empty or invalid OneTrust cookie", () => {
      // Set invalid OneTrust cookie
      cy.setCookie("OptanonConsent", "invalid&cookie&format");

      const overrides = {
        ot_fides_mapping: testOTMappingValue,
      };
      // Stub the experience with the following defaults:
      // analytics: true, advertising: false, essential: true
      cy.fixture("consent/experience_banner_modal.json").then((experience) => {
        stubConfig(
          {
            experience: experience.items[0],
          },
          null,
          null,
          undefined,
          { ...overrides },
        );
      });

      cy.waitUntilFidesInitialized().then(() => {
        // Open the modal
        cy.contains("button", "Manage preferences").click();

        // Verify Fides UI matches expected defaults
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });
      });
    });

    it("should handle malformed mapping configuration", () => {
      // Set OneTrust cookie
      cy.setCookie("OptanonConsent", otConsentCookieAllAccepted);

      const overrides = {
        ot_fides_mapping: "this-is-not-valid",
      };
      // Stub the experience with the following defaults:
      // analytics: true, advertising: false, essential: true
      cy.fixture("consent/experience_banner_modal.json").then((experience) => {
        stubConfig(
          {
            experience: experience.items[0],
          },
          null,
          null,
          undefined,
          { ...overrides },
        );
      });

      cy.waitUntilFidesInitialized().then(() => {
        // Banner should not exist since all notices have consents
        cy.get("div#fides-banner").should("not.exist");

        cy.get("#fides-modal-link").click();

        // Verify Fides UI matches expected defaults
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });
      });
    });

    it("should handle OneTrust categories that do not exist in mapping", () => {
      // Set OneTrust cookie with additional categories not in mapping
      cy.setCookie(
        "OptanonConsent",
        "OptanonConsent=groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0099%3A1",
      );

      const overrides = {
        ot_fides_mapping: testOTMappingValue,
      };
      // Stub the experience with the following defaults:
      // analytics: true, advertising: false, essential: true
      cy.fixture("consent/experience_banner_modal.json").then((experience) => {
        stubConfig(
          {
            experience: experience.items[0],
          },
          null,
          null,
          undefined,
          { ...overrides },
        );
      });

      cy.waitUntilFidesInitialized().then(() => {
        // Open the modal
        cy.contains("button", "Manage preferences").click();

        // Verify Fides UI matches expected defaults
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });
      });
      // C0003 and C0099 should not affect any Fides notices
    });
    it("should allow changing migrated preferences through the UI", () => {
      // Set OneTrust cookie with mixed preferences
      cy.setCookie("OptanonConsent", otConsentCookieMixed);

      // Set OneTrust cookie with all preferences rejected
      cy.setCookie("OptanonConsent", otConsentCookieAllRejected);

      const overrides = {
        ot_fides_mapping: testOTMappingValue,
      };
      // Stub the experience with the following defaults:
      // analytics: true, advertising: false, essential: true
      cy.fixture("consent/experience_banner_modal.json").then((experience) => {
        stubConfig(
          {
            experience: experience.items[0],
          },
          null,
          null,
          undefined,
          { ...overrides },
        );
      });

      cy.waitUntilFidesInitialized().then(() => {
        // Banner should not exist since all notices have consents
        cy.get("div#fides-banner").should("not.exist");

        cy.get("#fides-modal-link").click();

        // Verify Fides UI matches expected migration
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });

        // change 1 preference to true
        cy.getByTestId("toggle-Advertising").click();

        cy.getByTestId("Save-btn").click();
        // Modal should close after saving
        cy.getByTestId("consent-modal").should("not.be.visible");

        // Verify Fides cookie was created
        cy.getCookie("fides_consent").should("exist");
        // check that the cookie updated
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            expect(cookieKeyConsent.consent)
              .property(ADVERTISING_KEY)
              .is.eql(true);
            expect(cookieKeyConsent.consent)
              .property(ESSENTIAL_KEY)
              .is.eql(true);
            expect(cookieKeyConsent.consent)
              .property(ANALYTICS_KEY)
              .is.eql(false);
            expect(cookieKeyConsent.fides_meta)
              .property("consentMethod")
              .is.eql(ConsentMethod.SAVE);
          });
        });

        // check that window.Fides.consent updated
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [ADVERTISING_KEY]: true,
            [ESSENTIAL_KEY]: true,
            [ANALYTICS_KEY]: false,
          });

        // Reload the page but now we shouldn't need to pass in any OT override info
        cy.fixture("consent/experience_banner_modal.json").then(
          (experience) => {
            stubConfig({
              experience: experience.items[0],
            });
          },
        );

        cy.get("#fides-modal-link").click();

        // Verify Fides UI matches expected migration
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });
      });
    });
  });
});
