import { stubConfig } from "../support/stubs";

describe.skip("Fides.showModal", () => {
  describe("Overlay enabled", () => {
    beforeEach(() => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
        experience: {
          show_banner: false,
        },
      });
    });

    it("Should add 'fides-overlay-modal-link-shown' class to body", () => {
      cy.get("body").should("have.class", "fides-overlay-modal-link-shown");
    });

    it("Should allow showModal", () => {
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(100);
      cy.window().its("Fides").invoke("showModal");
      cy.get("@FidesUIShown").should("have.been.calledOnce");
      cy.get(".fides-modal-content").should("be.visible");
    });
  });

  describe("Overlay disabled", () => {
    beforeEach(() => {
      stubConfig({
        options: {
          isOverlayEnabled: false,
        },
        experience: {
          show_banner: false,
        },
      });
    });

    it("Should not add 'fides-overlay-modal-link-shown' class to body", () => {
      cy.get("body").should("not.have.class", "fides-overlay-modal-link-shown");
    });

    it("Should not allow showModal", () => {
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(100);
      cy.window().its("Fides").invoke("showModal");
      cy.get("@FidesUIShown").should("not.have.been.called");
      cy.get(".fides-modal-content").should("not.exist");
    });
  });
});
