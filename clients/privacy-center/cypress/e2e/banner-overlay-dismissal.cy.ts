import { ConsentMethod } from "fides-js";
import { stubConfig } from "../support/stubs";

function assertDismissCalled() {
  cy.get("@FidesUpdated")
    .should("have.been.calledOnce")
    .its("lastCall.args.0.detail.extraDetails.consentMethod")
    .then((consentMethod) => {
      expect(consentMethod).to.eql(ConsentMethod.dismiss);
    });

  cy.wait("@patchPrivacyPreference");
}

describe("Banner and overlay dismissal", () => {
  describe("Consent with dismissal allowed", () => {
    beforeEach(() => {
      stubConfig({
        options: {
          tcfEnabled: false,
          preventDismissal: false,
        },
      });
    });

    describe("Banner dismissal", () => {
      it("Should dismiss the banner by clicking the x", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("#fides-banner").within(() => {
          cy.get(".fides-close-button").click();
        });
        cy.get("#fides-banner").should("not.be.visible");

        assertDismissCalled();
      });

      it("Should not dismiss the banner by clicking outside", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("h1").click(); // click outside

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the banner by hitting ESC", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("body").type("{esc}");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });
    });

    describe("Overlay dismissal", () => {
      it("Should dismiss the banner by clicking the x", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get(".fides-modal-content").within(() => {
          cy.get(".fides-close-button").click();
        });
        cy.get(".fides-modal-content").should("not.be.visible");

        assertDismissCalled();
      });

      it("Should not dismiss the banner by clicking outside", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("h1").click({ force: true }); // click outside
        cy.get(".fides-modal-content").should("be.visible");
        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the banner by hitting ESC", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get("body").type("{esc}");
        cy.get(".fides-modal-content").should("be.visible");
        cy.get("@FidesUpdated").should("not.have.been.called");
      });
    });
  });

  describe("Consent with dismissal not allowed", () => {
    beforeEach(() => {
      stubConfig({
        options: {
          tcfEnabled: false,
          preventDismissal: true,
        },
      });
    });

    describe("Banner dismissal", () => {
      it("Should not show the x button", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("#fides-banner").within(() => {
          cy.get(".fides-close-button").should("not.be.visible");
        });

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the banner by clicking outside", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("h1").click({ force: true }); // click outside
        cy.get("#fides-banner").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the banner by hitting ESC", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("body").type("{esc}");
        cy.get("#fides-banner").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });
    });

    describe("Overlay dismissal", () => {
      it("Should not show the x button", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get(".fides-modal-content").within(() => {
          cy.get(".fides-close-button").should("not.be.visible");
        });

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the banner by clicking outside", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get(".fides-modal-overlay").click({ force: true });
        cy.get(".fides-modal-content").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the banner by hitting ESC", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get("body").type("{esc}");
        cy.get(".fides-modal-content").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });
    });
  });

  describe("TCF with dismissal allowed", () => {
    beforeEach(() => {
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            tcfEnabled: true,
            preventDismissal: false,
          },
          experience: experience.items[0],
        });
      });
    });

    describe("Banner dismissal", () => {
      it("Should dismiss the banner by clicking the x", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("#fides-banner").within(() => {
          cy.get(".fides-close-button").click();
        });
        cy.get("#fides-banner").should("not.be.visible");

        assertDismissCalled();
      });

      it("Should not dismiss the banner by clicking outside", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("h1").click(); // click outside
        cy.get("#fides-banner").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the banner by hitting ESC", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("body").type("{esc}");
        cy.get("#fides-banner").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });
    });

    describe("Overlay dismissal", () => {
      it("Should dismiss the overlay by clicking the x", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get(".fides-modal-content").within(() => {
          cy.get(".fides-close-button").click();
        });
        cy.get(".fides-modal-content").should("not.be.visible");

        assertDismissCalled();
      });

      it("Should not dismiss the overlay by clicking outside", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get(".fides-modal-overlay").click({ force: true });
        cy.get(".fides-modal-content").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the overlay by hitting ESC", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get("body").type("{esc}");
        cy.get(".fides-modal-content").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });
    });
  });

  describe("TCF with dismissal not allowed", () => {
    beforeEach(() => {
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            tcfEnabled: true,
            preventDismissal: true,
          },
          experience: experience.items[0],
        });
      });
    });

    describe("Banner dismissal", () => {
      it("Should not show the x button", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("#fides-banner").within(() => {
          cy.get(".fides-close-button").should("not.be.visible");
        });

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the banner by clicking outside", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("h1").click({ force: true }); // click outside
        cy.get("#fides-banner").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the banner by hitting ESC", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.get("body").type("{esc}");
        cy.get("#fides-banner").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });
    });

    describe("Overlay dismissal", () => {
      it("Should not show the x button", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get(".fides-modal-content").within(() => {
          cy.get(".fides-close-button").should("not.be.visible");
        });

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the overlay by clicking outside", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get(".fides-modal-overlay").click({ force: true });
        cy.get(".fides-modal-content").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });

      it("Should not dismiss the overlay by hitting ESC", () => {
        cy.get("#fides-banner").should("be.visible");
        cy.getByTestId("Manage preferences-btn").click();
        cy.get(".fides-modal-content").should("be.visible");
        cy.get("body").type("{esc}");
        cy.get(".fides-modal-content").should("be.visible");

        cy.get("@FidesUpdated").should("not.have.been.called");
      });
    });
  });
});
