import type { FidesEventDetail, FidesEventType } from "fides-js";
import { ConsentFlagType, ConsentNonApplicableFlagMode } from "fides-js";

import { stubConfig, stubTCFExperience } from "../support/stubs";

interface FidesEventExpectation {
  type: FidesEventType;
  detail: Partial<FidesEventDetail>;
}

describe("Consent FidesEvents", () => {
  /**
   * Verifies that all expected FidesEvents were fired in the correct sequence.
   *
   * Note: For event details, this uses a partial match (deep.include) to allow
   * for additional properties to exist in the actual events beyond what we specify.
   *
   * @example
   * const expectedEvents = [
   *   {
   *     type: "FidesUIShown",
   *     detail: {
   *       extraDetails: {
   *         servingComponent: "banner"
   *       }
   *     }
   *   }
   * ];
   * expectFidesEventSequence(expectedEvents);
   */
  function expectFidesEventSequence(expectedEvents: FidesEventExpectation[]) {
    cy.log("Verify the complete sequence of FidesEvents");
    cy.get("@AllFidesEvents").then((stub: any) => {
      const events = stub.getCalls().map((call) => ({
        type: call.args[0].type,
        detail: call.args[0].detail as FidesEventDetail,
      }));

      // For each event, verify only the properties we care about
      events.forEach((actual, index) => {
        const { type, detail: expectedDetail } = expectedEvents[index];
        expect(actual.type, `Event ${index} type`).to.equal(type);
        expect(actual.detail, `Event ${index} detail`).to.be.an("object");

        // Verify timestamp exists and is a valid performance.now() value
        expect(actual.detail.timestamp).to.be.a("number");

        // Only verify the properties we specified in expectedEvents
        Object.entries(expectedDetail).forEach(([key, value]) => {
          // First verify the key exists if we expect a value
          if (Object.keys(value).length > 0) {
            expect(actual.detail).to.have.property(key);
          }
          expect(
            actual.detail[key],
            `Event ${index} detail.${key}`,
          ).to.deep.include(value);
        });
      });

      // Verify the sequence of events matches exactly
      expect(
        events.map((e) => e.type),
        "Expected event types to match exactly in order",
      ).to.deep.equal(expectedEvents.map((e) => e.type));
    });
  }

  describe("when banner_and_modal experience", () => {
    beforeEach(() => {
      // Load the banner_and_modal experience
      const fixture = "experience_banner_modal.json";
      cy.fixture(`consent/${fixture}`).then((data) => {
        let experience = data.items[0];
        stubConfig({ experience });
      });
    });

    it("should fire FidesEvents for all key interactions", () => {
      const expectedEvents: FidesEventExpectation[] = [];

      // Initialize and show banner on page load
      expectedEvents.push(
        { type: "FidesInitializing", detail: {} },
        { type: "FidesReady", detail: {} },
        { type: "FidesInitialized", detail: {} },
        {
          type: "FidesUIShown",
          detail: {
            extraDetails: {
              servingComponent: "banner",
              trigger: { origin: "fides" }, // automatically opened by fides-js
            },
          },
        },
      );

      // Open modal from banner button
      cy.get("#fides-banner .fides-manage-preferences-button").click();
      expectedEvents.push({
        type: "FidesUIShown",
        detail: {
          extraDetails: {
            servingComponent: "modal",
            trigger: {
              type: "button",
              label: "Manage preferences",
              origin: "fides",
            },
          },
        },
      });

      // Toggle Advertising notice on then off
      cy.getByTestId("toggle-Advertising").click().click();
      // cy.get("#fides-modal .fides-toggle-input").first().click().click();
      expectedEvents.push(
        {
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "modal",
              trigger: {
                type: "toggle",
                label: "Advertising",
                checked: true,
                origin: "fides",
              },
              preference: {
                key: "advertising",
                type: "notice",
              },
            },
          },
        },
        {
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "modal",
              trigger: {
                type: "toggle",
                label: "Advertising",
                checked: false,
                origin: "fides",
              },
              preference: {
                key: "advertising",
                type: "notice",
              },
            },
          },
        },
      );

      // Toggle second notice off (Analytics opt out)
      cy.get("#fides-modal .fides-toggle-input").eq(2).click();
      expectedEvents.push({
        type: "FidesUIChanged",
        detail: {
          extraDetails: {
            servingComponent: "modal",
            trigger: {
              type: "toggle",
              label: "Analytics",
              checked: false,
              origin: "fides",
            },
            preference: {
              key: "analytics_opt_out",
              type: "notice",
            },
          },
        },
      });

      // Save current preference selections
      cy.get("#fides-modal #fides-save-button").click();
      expectedEvents.push(
        { type: "FidesModalClosed", detail: {} },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "save",
              servingComponent: "modal",
              trigger: {
                label: "Save",
                origin: "fides",
                type: "button",
              },
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "save",
              servingComponent: "modal",
              trigger: {
                label: "Save",
                origin: "fides",
                type: "button",
              },
            },
          },
        },
      );

      // Open modal from link
      cy.get("#fides-modal-link").click();
      expectedEvents.push({
        type: "FidesUIShown",
        detail: {
          extraDetails: {
            servingComponent: "modal",
            trigger: { origin: "external" },
          },
        },
      });

      // Click opt-out button to reject all notices
      cy.get(".fides-modal-button-group").contains("Opt out of all").click();
      expectedEvents.push(
        { type: "FidesModalClosed", detail: {} },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "reject",
              servingComponent: "modal",
              trigger: {
                type: "button",
                label: "Opt out of all",
                origin: "fides",
              },
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "reject",
              servingComponent: "modal",
              trigger: {
                type: "button",
                label: "Opt out of all",
                origin: "fides",
              },
            },
          },
        },
      );

      // Reopen modal from link
      cy.get("#fides-modal-link").click();
      expectedEvents.push({
        type: "FidesUIShown",
        detail: {
          extraDetails: {
            servingComponent: "modal",
            trigger: { origin: "external" },
          },
        },
      });

      // Click opt-in button to accept all notices
      cy.get(".fides-modal-button-group").contains("Opt in to all").click();
      expectedEvents.push(
        { type: "FidesModalClosed", detail: {} },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "accept",
              servingComponent: "modal",
              trigger: {
                type: "button",
                label: "Opt in to all",
                origin: "fides",
              },
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "accept",
              servingComponent: "modal",
              trigger: {
                type: "button",
                label: "Opt in to all",
                origin: "fides",
              },
            },
          },
        },
      );

      // Open modal from Fides.showModal()
      cy.window().then((win) => {
        win.Fides.showModal();
      });
      expectedEvents.push({
        type: "FidesUIShown",
        detail: {
          extraDetails: {
            servingComponent: "modal",
            trigger: { origin: "external" },
          },
        },
      });

      // Update preferences from Fides.updateConsent()
      cy.window().then(async (win) => {
        await win.Fides.updateConsent({
          consent: {
            analytics_opt_out: false,
          },
        });
      });
      expectedEvents.push(
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "script",
              trigger: { origin: "external" },
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "script",
              trigger: { origin: "external" },
            },
          },
        },
      );

      expectFidesEventSequence(expectedEvents);
    });
  });

  describe("when tcf_overlay experience", () => {
    beforeEach(() => {
      // Load the tcf_overlay experience, adding an example AC vendor
      cy.fixture("consent/experience_tcf.json").then((payload) => {
        const experience = payload.items[0];
        const acVendor = {
          id: "gacp.89",
          has_vendor_id: true,
          name: "Meta",
          description: null,
          vendor_deleted_date: null,
          default_preference: "opt_out",
          purpose_consents: [],
        };
        experience.tcf_vendor_consents.push(acVendor);
        experience.tcf_vendor_relationships.push(acVendor);
        stubTCFExperience({ experienceFullOverride: experience });
      });
    });

    it("should fire FidesEvents for all key interactions", () => {
      const expectedEvents: FidesEventExpectation[] = [];

      // Initialize and show TCF banner on page load
      expectedEvents.push(
        { type: "FidesInitializing", detail: {} },
        { type: "FidesReady", detail: {} },
        { type: "FidesInitialized", detail: {} },
        {
          type: "FidesUIShown",
          detail: { extraDetails: { servingComponent: "tcf_banner" } },
        },
      );

      // Open TCF modal from banner button
      cy.get(".fides-manage-preferences-button").click();
      expectedEvents.push({
        type: "FidesUIShown",
        detail: { extraDetails: { servingComponent: "tcf_overlay" } },
      });

      // Toggle first purpose on then off
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .first()
        .click()
        .click();
      expectedEvents.push(
        {
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "tcf_overlay",
              trigger: {
                type: "toggle",
                label: "Use profiles to select personalised advertising",
                checked: true,
                origin: "fides",
              },
              preference: {
                key: "tcf_purpose_consent_4",
                type: "tcf_purpose_consent",
              },
            },
          },
        },
        {
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "tcf_overlay",
              trigger: {
                type: "toggle",
                label: "Use profiles to select personalised advertising",
                checked: false,
                origin: "fides",
              },
              preference: {
                key: "tcf_purpose_consent_4",
                type: "tcf_purpose_consent",
              },
            },
          },
        },
      );

      // Toggle second purpose on
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .eq(1)
        .click();
      expectedEvents.push({
        type: "FidesUIChanged",
        detail: {
          extraDetails: {
            servingComponent: "tcf_overlay",
            trigger: {
              type: "toggle",
              label: "Use profiles to select personalised content",
              checked: true,
              origin: "fides",
            },
            preference: {
              key: "tcf_purpose_consent_6",
              type: "tcf_purpose_consent",
            },
          },
        },
      });

      // Switch to legitimate interest purposes tab
      cy.get(".fides-radio-button-group button")
        .contains("Legitimate interest")
        .click();
      // No event

      // Toggle third purpose off (legitimate interest)
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .first()
        .click();
      expectedEvents.push({
        type: "FidesUIChanged",
        detail: {
          extraDetails: {
            servingComponent: "tcf_overlay",
            trigger: {
              type: "toggle",
              label: "Use limited data to select advertising",
              checked: false,
              origin: "fides",
            },
            preference: {
              key: "tcf_purpose_legitimate_interest_2",
              type: "tcf_purpose_legitimate_interest",
            },
          },
        },
      });

      // Switch to special features tab
      cy.get("#fides-tab-features").click();
      // No event

      // Expand first feature description
      cy.getByTestId("records-list-features").first().click();
      // No event

      // Switch to vendors tab
      cy.get("#fides-tab-vendors").click();
      // No event

      // Toggle GVL vendor Captify on then off
      cy.getByTestId("toggle-Captify")
        .find(".fides-toggle-input")
        .click()
        .click();
      expectedEvents.push(
        {
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "tcf_overlay",
              trigger: {
                type: "toggle",
                label: "Captify",
                checked: true,
                origin: "fides",
              },
              preference: {
                key: "gvl.2",
                type: "tcf_vendor_consent",
                vendor_id: "gvl.2",
                vendor_list: "gvl",
                vendor_list_id: "2",
                vendor_name: "Captify",
              },
            },
          },
        },
        {
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "tcf_overlay",
              trigger: {
                type: "toggle",
                label: "Captify",
                checked: false,
                origin: "fides",
              },
              preference: {
                key: "gvl.2",
                type: "tcf_vendor_consent",
                vendor_id: "gvl.2",
                vendor_list: "gvl",
                vendor_list_id: "2",
                vendor_name: "Captify",
              },
            },
          },
        },
      );

      // Toggle AC vendor Meta on then off
      cy.getByTestId("toggle-Meta").find(".fides-toggle-input").click().click();
      expectedEvents.push(
        {
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "tcf_overlay",
              trigger: {
                type: "toggle",
                label: "Meta",
                checked: true,
                origin: "fides",
              },
              preference: {
                key: "gacp.89",
                type: "tcf_vendor_consent",
                vendor_id: "gacp.89",
                vendor_list: "gacp",
                vendor_list_id: "89",
                vendor_name: "Meta",
              },
            },
          },
        },
        {
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "tcf_overlay",
              trigger: {
                type: "toggle",
                label: "Meta",
                checked: false,
                origin: "fides",
              },
              preference: {
                key: "gacp.89",
                type: "tcf_vendor_consent",
                vendor_id: "gacp.89",
                vendor_list: "gacp",
                vendor_list_id: "89",
                vendor_name: "Meta",
              },
            },
          },
        },
      );

      // Save current TCF preferences
      cy.getByTestId("Save-btn").click();
      expectedEvents.push(
        { type: "FidesModalClosed", detail: {} },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "save",
              servingComponent: "tcf_overlay",
              trigger: {
                type: "button",
                label: "Save",
                origin: "fides",
              },
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "save",
              servingComponent: "tcf_overlay",
              trigger: {
                type: "button",
                label: "Save",
                origin: "fides",
              },
            },
          },
        },
      );

      // Open TCF modal from link
      cy.get("#fides-modal-link").click();
      expectedEvents.push({
        type: "FidesUIShown",
        detail: { extraDetails: { servingComponent: "tcf_overlay" } },
      });

      // Click opt-out button to reject all
      cy.get(".fides-modal-button-group").contains("Opt out of all").click();
      expectedEvents.push(
        { type: "FidesModalClosed", detail: {} },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "reject",
              servingComponent: "tcf_overlay",
              trigger: {
                type: "button",
                label: "Opt out of all",
                origin: "fides",
              },
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "reject",
              servingComponent: "tcf_overlay",
              trigger: {
                type: "button",
                label: "Opt out of all",
                origin: "fides",
              },
            },
          },
        },
      );

      // Reopen TCF modal from link
      cy.get("#fides-modal-link").click();
      expectedEvents.push({
        type: "FidesUIShown",
        detail: { extraDetails: { servingComponent: "tcf_overlay" } },
      });

      // Click opt-in button to accept all
      cy.get(".fides-modal-button-group").contains("Opt in to all").click();
      expectedEvents.push(
        { type: "FidesModalClosed", detail: {} },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "accept",
              servingComponent: "tcf_overlay",
              trigger: {
                type: "button",
                label: "Opt in to all",
                origin: "fides",
              },
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "accept",
              servingComponent: "tcf_overlay",
              trigger: {
                type: "button",
                label: "Opt in to all",
                origin: "fides",
              },
            },
          },
        },
      );

      expectFidesEventSequence(expectedEvents);
    });
  });

  describe("when tcf_overlay experience with custom purposes", () => {
    beforeEach(() => {
      // Load the tcf_overlay experience with custom purposes enabled
      cy.fixture("consent/experience_tcf.json").then((payload) => {
        const experience = payload.items[0];
        stubTCFExperience({
          experienceFullOverride: experience,
          includeCustomPurposes: true,
        });
      });
    });

    it("should use notice_key in FidesUIChanged events for custom purposes", () => {
      const expectedEvents: FidesEventExpectation[] = [
        { type: "FidesInitializing", detail: {} },
        { type: "FidesReady", detail: {} },
        { type: "FidesInitialized", detail: {} },
        {
          type: "FidesUIShown",
          detail: { extraDetails: { servingComponent: "tcf_banner" } },
        },
      ];

      // Open TCF modal and toggle the custom purpose
      cy.get(".fides-manage-preferences-button").click();
      expectedEvents.push({
        type: "FidesUIShown",
        detail: { extraDetails: { servingComponent: "tcf_overlay" } },
      });

      cy.getByTestId("toggle-Advertising English")
        .find(".fides-toggle-input")
        .click();

      expectedEvents.push({
        type: "FidesUIChanged",
        detail: {
          extraDetails: {
            servingComponent: "tcf_overlay",
            trigger: {
              type: "toggle",
              label: "Advertising English",
              checked: true,
              origin: "fides",
            },
            preference: {
              key: "advertising", // Should use notice_key instead of ID
              type: "notice",
            },
          },
        },
      });

      expectFidesEventSequence(expectedEvents);
    });
  });

  describe("when using consent mechanism flags and non-applicable notices", () => {
    beforeEach(() => {
      // Load the banner_and_modal experience
      const fixture = "experience_banner_modal.json";
      cy.fixture(`consent/${fixture}`).then((data) => {
        let experience = data.items[0];

        // Add non-applicable privacy notices
        experience.non_applicable_privacy_notices = [
          "essential",
          "personalization",
        ];

        stubConfig({
          experience,
          options: {
            fidesConsentFlagType: ConsentFlagType.CONSENT_MECHANISM,
            fidesConsentNonApplicableFlagMode:
              ConsentNonApplicableFlagMode.INCLUDE,
          },
        });
      });
    });

    it("should correctly format consent values in events based on flag type and mode", () => {
      // Create our array of expected events
      const expectedEvents: FidesEventExpectation[] = [];

      // Initialize and show banner
      expectedEvents.push(
        { type: "FidesInitializing", detail: {} },
        { type: "FidesReady", detail: {} },
        { type: "FidesInitialized", detail: {} },
        {
          type: "FidesUIShown",
          detail: { extraDetails: { servingComponent: "banner" } },
        },
      );

      // Open modal from banner button
      cy.get("#fides-banner .fides-manage-preferences-button").click();
      expectedEvents.push({
        type: "FidesUIShown",
        detail: { extraDetails: { servingComponent: "modal" } },
      });

      // Save preferences - this should trigger FidesUpdating and FidesUpdated events
      cy.get("#fides-modal #fides-save-button").click();
      expectedEvents.push(
        { type: "FidesModalClosed", detail: {} },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "save",
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "save",
            },
          },
        },
      );

      // Verify the sequence of events
      cy.log(
        "Verify FidesUpdated event has correctly formatted consent values",
      );
      cy.get("@AllFidesEvents").then((stub: any) => {
        // Get the FidesUpdated event
        const updatedEvent = stub
          .getCalls()
          .find((call) => call.args[0].type === "FidesUpdated");
        expect(updatedEvent).to.exist;

        const { detail } = updatedEvent.args[0];

        // Check consent formatting - values should be strings like "opt_in" not booleans
        expect(detail.consent).to.be.an("object");
        Object.values(detail.consent).forEach((value) => {
          expect(value).to.be.a("string");
        });

        // Verify consent contains values for applicable notices with string mechanisms
        expect(detail.consent).to.have.any.keys([
          "advertising",
          "analytics_opt_out",
        ]);

        // Verify non-applicable notices are included with "not_applicable" value
        expect(detail.consent).to.include.keys("essential", "personalization");
        expect(detail.consent.essential).to.equal("acknowledge");
        expect(detail.consent.personalization).to.equal("not_applicable");
      });
    });
  });
});
