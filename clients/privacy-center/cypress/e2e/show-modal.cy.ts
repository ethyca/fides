import { CONSENT_COOKIE_NAME } from "fides-js";

import { stubConfig } from "../support/stubs";

describe("Fides.showModal", () => {
  describe("Overlay enabled", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
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
      cy.getByTestId("consent-modal").should("be.visible");
    });

    describe("Default modal link is disabled", () => {
      beforeEach(() => {
        stubConfig({
          options: {
            modalLinkId: "",
          },
        });
      });

      it("Should not show modal link in favor of showModal", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(100);
        cy.window().its("Fides").invoke("showModal");
        cy.get("@FidesUIShown").should("have.been.called");
      });
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
      cy.getByTestId("consent-modal").should("not.exist");
    });
  });
});
