import { stubConfig, stubTCFExperience } from "../support/stubs";

describe("Consent events", () => {
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

      // Verify the complete sequence of events
      cy.get("@AllFidesEvents")
        .should("have.been.called")
        .then((stub: any) => {
          const events = stub.getCalls().map((call) => call.args[0].type);
          expect(events).to.deep.equal([
            "FidesInitializing",
            "FidesInitialized",
            "FidesUIShown", // banner
            "FidesUIShown", // modal
            "FidesUIChanged", // toggle click
            "FidesModalClosed", // save
            "FidesUpdating", // updating
            "FidesUpdated", // updated
          ]);
        });
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
      // TODO: Implement this
    });
  });
});
