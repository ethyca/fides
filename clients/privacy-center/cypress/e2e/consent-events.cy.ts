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

        // Verify timestamp exists and is a valid performance.now() value
        expect(actual.detail.timestamp).to.be.a("number").and.to.be.at.least(0);

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
      // 1. Initialize and show banner
      cy.get("@FidesInitializing").should("have.callCount", 1);
      cy.get("@FidesInitialized").should("have.callCount", 1);
      cy.get("@FidesUIShown").should("have.callCount", 1);

      // 2. Open modal from banner
      cy.get("#fides-banner .fides-manage-preferences-button").click();
      cy.get("@FidesUIShown").should("have.callCount", 2);

      // 3. Toggle first notice on & off
      cy.get("#fides-modal .fides-toggle-input").first().click();
      cy.get("@FidesUIChanged").should("have.callCount", 1);
      cy.get("#fides-modal .fides-toggle-input").first().click();
      cy.get("@FidesUIChanged").should("have.callCount", 2);

      // 4. Toggle second notice on
      cy.get("#fides-modal .fides-toggle-input").eq(1).click();
      cy.get("@FidesUIChanged").should("have.callCount", 3);

      // 5. Save preferences
      cy.get("#fides-modal .fides-save-button").click();
      cy.get("@FidesModalClosed").should("have.callCount", 1);
      cy.get("@FidesUpdating").should("have.callCount", 1);
      cy.get("@FidesUpdated").should("have.callCount", 1);

      // 6. Re-open modal
      cy.get("#fides-modal-link").click();
      cy.get("@FidesUIShown").should("have.callCount", 3);

      // 7. Opt-out of all
      cy.get(".fides-modal-button-group").contains("Opt out of all").click();
      cy.get("@FidesModalClosed").should("have.callCount", 2);
      cy.get("@FidesUpdating").should("have.callCount", 2);
      cy.get("@FidesUpdated").should("have.callCount", 2);

      // 8. Re-open modal
      cy.get("#fides-modal-link").click();
      cy.get("@FidesUIShown").should("have.callCount", 4);

      // 9. Opt-in to all
      cy.get(".fides-modal-button-group").contains("Opt in to all").click();
      cy.get("@FidesModalClosed").should("have.callCount", 3);
      cy.get("@FidesUpdating").should("have.callCount", 3);
      cy.get("@FidesUpdated").should("have.callCount", 3);

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
        // UI Changed events from toggling notices
        ...[...Array(3)].map(() => ({
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "modal",
            },
          },
        })),
        // First save
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
        // Re-open modal
        {
          type: "FidesUIShown",
          detail: {
            extraDetails: {
              servingComponent: "modal",
            },
          },
        },
        // Reject all
        {
          type: "FidesModalClosed",
          detail: {},
        },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "reject",
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "reject",
            },
          },
        },
        // Re-open modal
        {
          type: "FidesUIShown",
          detail: {
            extraDetails: {
              servingComponent: "modal",
            },
          },
        },
        // Accept all
        {
          type: "FidesModalClosed",
          detail: {},
        },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "accept",
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "accept",
            },
          },
        },
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
      cy.get("@FidesInitializing").should("have.callCount", 1);
      cy.get("@FidesInitialized").should("have.callCount", 1);
      cy.get("@FidesUIShown").should("have.callCount", 1);

      // 2. Open preferences modal
      cy.get(".fides-manage-preferences-button").click();
      cy.get("@FidesUIShown").should("have.callCount", 2);

      // 3. Toggle first purpose on & off
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .first()
        .click();
      cy.get("@FidesUIChanged").should("have.callCount", 1);
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .first()
        .click();
      cy.get("@FidesUIChanged").should("have.callCount", 2);

      // 4. Toggle second purpose on
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .eq(1)
        .click();
      cy.get("@FidesUIChanged").should("have.callCount", 3);

      // 5. Switch to legitimate interest tab
      cy.get(".fides-radio-button-group button")
        .contains("Legitimate interest")
        .click();

      // 6. Toggle third purpose on
      cy.getByTestId("records-list-purposes")
        .find(".fides-toggle-input")
        .first()
        .click();
      cy.get("@FidesUIChanged").should("have.callCount", 4);

      // 7. Switch to features tab
      cy.get("#fides-tab-features").click();

      // 8. Expand features description
      cy.getByTestId("records-list-features").first().click();

      // 9. Switch to vendors tab
      cy.get("#fides-tab-vendors").click();

      // 10. Toggle GVL vendor on & off
      cy.getByTestId("toggle-Captify").find(".fides-toggle-input").click();
      cy.get("@FidesUIChanged").should("have.callCount", 5);
      cy.getByTestId("toggle-Captify").find(".fides-toggle-input").click();
      cy.get("@FidesUIChanged").should("have.callCount", 6);

      // 11. Toggle AC vendor on & off
      cy.getByTestId("toggle-Meta").find(".fides-toggle-input").click();
      cy.get("@FidesUIChanged").should("have.callCount", 7);
      cy.getByTestId("toggle-Meta").find(".fides-toggle-input").click();
      cy.get("@FidesUIChanged").should("have.callCount", 8);

      // 12. Save changes
      cy.getByTestId("Save-btn").click();
      cy.get("@FidesModalClosed").should("have.callCount", 1);
      cy.get("@FidesUpdating").should("have.callCount", 1);
      cy.get("@FidesUpdated").should("have.callCount", 1);

      // 13. Re-open modal
      cy.get("#fides-modal-link").click();
      cy.get("@FidesUIShown").should("have.callCount", 3);

      // 14. Opt-out of all
      cy.get(".fides-modal-button-group").contains("Opt out of all").click();
      cy.get("@FidesModalClosed").should("have.callCount", 2);
      cy.get("@FidesUpdating").should("have.callCount", 2);
      cy.get("@FidesUpdated").should("have.callCount", 2);

      // 15. Re-open modal
      cy.get("#fides-modal-link").click();
      cy.get("@FidesUIShown").should("have.callCount", 4);

      // 16. Opt-in to all
      cy.get(".fides-modal-button-group").contains("Opt in to all").click();
      cy.get("@FidesModalClosed").should("have.callCount", 3);
      cy.get("@FidesUpdating").should("have.callCount", 3);
      cy.get("@FidesUpdated").should("have.callCount", 3);

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
              servingComponent: "tcf_banner",
            },
          },
        },
        {
          type: "FidesUIShown",
          detail: {
            extraDetails: {
              servingComponent: "tcf_overlay",
            },
          },
        },
        // UI Changed events from toggling purposes and vendors
        ...[...Array(8)].map(() => ({
          type: "FidesUIChanged",
          detail: {
            extraDetails: {
              servingComponent: "modal", // TODO: This is a surprising result, but it's what we get
            },
          },
        })),
        // First save
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
        // Re-open modal
        {
          type: "FidesUIShown",
          detail: {
            extraDetails: {
              servingComponent: "tcf_overlay",
            },
          },
        },
        // Reject all
        {
          type: "FidesModalClosed",
          detail: {},
        },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "reject",
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "reject",
            },
          },
        },
        // Re-open modal
        {
          type: "FidesUIShown",
          detail: {
            extraDetails: {
              servingComponent: "tcf_overlay",
            },
          },
        },
        // Accept all
        {
          type: "FidesModalClosed",
          detail: {},
        },
        {
          type: "FidesUpdating",
          detail: {
            extraDetails: {
              consentMethod: "accept",
            },
          },
        },
        {
          type: "FidesUpdated",
          detail: {
            extraDetails: {
              consentMethod: "accept",
            },
          },
        },
      ];

      verifyFidesEventSequence(expectedEvents);
    });
  });
});
