import type { FidesEvent, FidesEventDetail } from "fides-js/src/lib/events";

import { stubConfig, stubTCFExperience } from "../support/stubs";

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
  function verifyFidesEventSequence(
    expectedEvents: Array<{ type: string; detail: Partial<FidesEventDetail> }>,
  ) {
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
      ).to.deep.equal(expectedEvents.map((e) => e.type));

      // For each event, verify only the properties we care about
      events.forEach((actual, index) => {
        const expected = expectedEvents[index];
        expect(actual.detail, `Event ${index} detail`).to.be.an("object");

        // Only verify the properties we specified in expectedEvents
        Object.entries(expected.detail).forEach(([key, value]) => {
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
      cy.get("@FidesInitializing").should("have.been.calledOnce");
      cy.get("@FidesInitialized").should("have.been.calledOnce");

      // Opening preferences modal should fire UIShown
      cy.get("#fides-banner .fides-manage-preferences-button").click();
      cy.get("@FidesUIShown").should("have.been.called");

      // Toggling a notice should fire UIChanged
      cy.get("#fides-modal .fides-toggle-input").first().click();
      cy.get("@FidesUIChanged").should("have.been.called");

      // Saving preferences should fire Updating and Updated
      cy.get("#fides-modal .fides-save-button").click();
      cy.get("@FidesModalClosed").should("have.been.called");
      cy.get("@FidesUpdating").should("have.been.called");
      cy.get("@FidesUpdated").should("have.been.called");

      const expectedEvents = [
        {
          type: "FidesInitializing",
          detail: {},
        },
        {
          type: "FidesInitialized",
          detail: {},
        },
        {
          type: "FidesUIShown",
          detail: {
            extraDetails: {
              servingComponent: "banner",
            },
          },
        },
        {
          type: "FidesUIShown",
          detail: {
            extraDetails: {
              servingComponent: "modal",
            },
          },
        },
        {
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "modal",
            },
          },
        },
        {
          type: "FidesModalClosed",
          detail: {},
        },
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
      ];

      verifyFidesEventSequence(expectedEvents);
    });
  });

  describe("when tcf_overlay experience", () => {
    beforeEach(() => {
      // Load the tcf_overlay experience
      stubTCFExperience({
        stubOptions: {
          tcfEnabled: true,
        },
      });
    });

    it("should fire FidesEvents for all key interactions", () => {
      // TODO: Add interaction steps

      const expectedEvents = [
        {
          type: "FidesInitializing",
          detail: {},
        },
        {
          type: "FidesInitialized",
          detail: {},
        },
        // TODO: Add more expected events for TCF overlay experience
      ];

      verifyFidesEventSequence(expectedEvents);
    });
  });
});
