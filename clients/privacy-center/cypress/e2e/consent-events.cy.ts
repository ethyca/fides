import type { FidesEventDetail, FidesEventType } from "fides-js/src/lib/events";

import { stubConfig, stubTCFExperience } from "../support/stubs";

type FidesEventTuple = [FidesEventType, Partial<FidesEventDetail>];

describe("Consent FidesEvents", () => {
  /**
   * Verifies that all expected FidesEvents were fired in the correct sequence.
   *
   * This helper checks that:
   * 1. Each event type matches exactly
   * 2. Each event's detail object contains at least the specified properties
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
   * verifyFidesEventSequence(expectedEvents);
   */
  function verifyFidesEventSequence(expectedEvents: FidesEventTuple[]) {
    cy.log("Verify the complete sequence of FidesEvents");
    cy.get("@AllFidesEvents").then((stub: any) => {
      const events = stub.getCalls().map((call) => ({
        type: call.args[0].type,
        detail: call.args[0].detail as FidesEventDetail,
      }));

      // First verify the sequence of events matches exactly
      expect(
        events.map((e) => e.type),
        "Expected event types to match exactly in order",
      ).to.deep.equal(expectedEvents.map((e) => e[0]));

      // For each event, verify only the properties we care about
      events.forEach((actual, index) => {
        const [, expectedDetail] = expectedEvents[index];
        expect(actual.detail, `Event ${index} detail`).to.be.an("object");

        // Verify timestamp exists and is a valid performance.now() value
        expect(actual.detail.timestamp).to.be.a("number").and.to.be.at.least(0);

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
      // 1. Initialize and show banner

      // 2. Open modal from banner
      cy.get("#fides-banner .fides-manage-preferences-button").click();

      // 3. Toggle first notice on & off
      cy.get("#fides-modal .fides-toggle-input").first().click().click();

      // 4. Toggle second notice on
      cy.get("#fides-modal .fides-toggle-input").eq(1).click();

      // 5. Save preferences
      cy.get("#fides-modal .fides-save-button").click();

      // 6. Re-open modal
      cy.get("#fides-modal-link").click();

      // 7. Opt-out of all
      cy.get(".fides-modal-button-group").contains("Opt out of all").click();

      // 8. Re-open modal
      cy.get("#fides-modal-link").click();

      // 9. Opt-in to all
      cy.get(".fides-modal-button-group").contains("Opt in to all").click();

      const expectedEvents: FidesEventTuple[] = [
        ["FidesInitializing", {}],
        ["FidesInitialized", {}],
        ["FidesUIShown", { extraDetails: { servingComponent: "banner" } }],
        ["FidesUIShown", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesModalClosed", {}],
        ["FidesUpdating", { extraDetails: { consentMethod: "save" } }],
        ["FidesUpdated", { extraDetails: { consentMethod: "save" } }],
        ["FidesUIShown", { extraDetails: { servingComponent: "modal" } }],
        ["FidesModalClosed", {}],
        ["FidesUpdating", { extraDetails: { consentMethod: "reject" } }],
        ["FidesUpdated", { extraDetails: { consentMethod: "reject" } }],
        ["FidesUIShown", { extraDetails: { servingComponent: "modal" } }],
        ["FidesModalClosed", {}],
        ["FidesUpdating", { extraDetails: { consentMethod: "accept" } }],
        ["FidesUpdated", { extraDetails: { consentMethod: "accept" } }],
      ];

      verifyFidesEventSequence(expectedEvents);
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
      // 1. Banner auto-shown

      // 2. Open preferences modal
      cy.get(".fides-manage-preferences-button").click();

      // 3. Toggle first purpose on & off
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .first()
        .click()
        .click();

      // 4. Toggle second purpose on
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .eq(1)
        .click();

      // 5. Switch to legitimate interest tab
      cy.get(".fides-radio-button-group button")
        .contains("Legitimate interest")
        .click();

      // 6. Toggle third purpose on
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .first()
        .click();

      // 7. Switch to features tab
      cy.get("#fides-tab-features").click();

      // 8. Expand features description
      cy.getByTestId("records-list-features").first().click();

      // 9. Switch to vendors tab
      cy.get("#fides-tab-vendors").click();

      // 10. Toggle GVL vendor on & off
      cy.getByTestId("toggle-Captify")
        .find(".fides-toggle-input")
        .click()
        .click();

      // 11. Toggle AC vendor on & off
      cy.getByTestId("toggle-Meta").find(".fides-toggle-input").click().click();

      // 12. Save changes
      cy.getByTestId("Save-btn").click();

      // 13. Re-open modal
      cy.get("#fides-modal-link").click();

      // 14. Opt-out of all
      cy.get(".fides-modal-button-group").contains("Opt out of all").click();

      // 15. Re-open modal
      cy.get("#fides-modal-link").click();

      // 16. Opt-in to all
      cy.get(".fides-modal-button-group").contains("Opt in to all").click();

      const expectedEvents: FidesEventTuple[] = [
        ["FidesInitializing", {}],
        ["FidesInitialized", {}],
        ["FidesUIShown", { extraDetails: { servingComponent: "tcf_banner" } }],
        ["FidesUIShown", { extraDetails: { servingComponent: "tcf_overlay" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesUIChanged", { extraDetails: { servingComponent: "modal" } }],
        ["FidesModalClosed", {}],
        ["FidesUpdating", { extraDetails: { consentMethod: "save" } }],
        ["FidesUpdated", { extraDetails: { consentMethod: "save" } }],
        ["FidesUIShown", { extraDetails: { servingComponent: "tcf_overlay" } }],
        ["FidesModalClosed", {}],
        ["FidesUpdating", { extraDetails: { consentMethod: "reject" } }],
        ["FidesUpdated", { extraDetails: { consentMethod: "reject" } }],
        ["FidesUIShown", { extraDetails: { servingComponent: "tcf_overlay" } }],
        ["FidesModalClosed", {}],
        ["FidesUpdating", { extraDetails: { consentMethod: "accept" } }],
        ["FidesUpdated", { extraDetails: { consentMethod: "accept" } }],
      ];

      verifyFidesEventSequence(expectedEvents);
    });
  });
});
