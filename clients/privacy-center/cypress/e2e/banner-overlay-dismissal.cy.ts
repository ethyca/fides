import { ConsentMethod, CONSENT_COOKIE_NAME, FidesCookie } from "fides-js";
import { stubConfig } from "../support/stubs";

function assertDismissCalled() {
  cy.get("@FidesUpdated")
    .should("have.been.calledOnce")
    .its("lastCall.args.0.detail.extraDetails.consentMethod")
    .then((consentMethod) => {
      expect(consentMethod).to.eql(ConsentMethod.DISMISS);
    });

  cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
    cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
      const fidesCookie: FidesCookie = JSON.parse(
        decodeURIComponent(cookie!.value)
      );
      expect(fidesCookie.fides_meta)
        .property("consentMethod")
        .is.eql(ConsentMethod.DISMISS);
    });
  });

  cy.wait("@patchPrivacyPreference");
}

describe("Banner and modal dismissal", () => {
  interface TestCaseOptions {
    tcfEnabled: boolean,
    preventDismissal: boolean,
  };

  // Test all combinations of TCF enabled/disabled and prevent dismissal enabled/disabled
  [
    { tcfEnabled: false, preventDismissal: false },
    { tcfEnabled: false, preventDismissal: true },
    { tcfEnabled: true, preventDismissal: false },
    { tcfEnabled: true, preventDismissal: true },
  ].forEach(({ tcfEnabled, preventDismissal }) => {
    describe(`when tcfEnabled is ${tcfEnabled} and preventDismissal is ${preventDismissal}`, () => {
      beforeEach(() => {
        if (!tcfEnabled) {
          stubConfig({
            options: {
              tcfEnabled: false,
              preventDismissal: preventDismissal,
            },
          });
        } else {
          cy.fixture("consent/experience_tcf.json").then((experience) => {
            stubConfig({
              options: {
                tcfEnabled: true,
                preventDismissal: preventDismissal,
              },
              experience: experience.items[0],
            });
          });
        }
      });

      if (!preventDismissal) {
        /**
         * Tests for the default case, when dismissal is allowed
         */
        describe("when using the banner", () => {
          it("should dismiss the banner by clicking the x", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.get("#fides-banner").within(() => {
              cy.get(".fides-close-button").click();
            });
            cy.get("#fides-banner").should("not.be.visible");

            assertDismissCalled();
          });

          it("should dismiss the banner by clicking outside", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.get("h1").click(); // click outside
            cy.get("#fides-banner").should("not.be.visible");

            assertDismissCalled();
          });

          it("should dismiss the banner by hitting ESC", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.get("body").type("{esc}");
            cy.get("#fides-banner").should("not.be.visible");

            assertDismissCalled();
          });
        });

        describe("when using the modal", () => {
          it("should dismiss the modal by clicking the x", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.getByTestId("Manage preferences-btn").click();
            cy.get(".fides-modal-content").should("be.visible");
            cy.get(".fides-modal-content").within(() => {
              cy.get(".fides-close-button").click();
            });
            cy.get(".fides-modal-content").should("not.be.visible");

            assertDismissCalled();
          });

          it("should dismiss the modal by clicking outside", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.getByTestId("Manage preferences-btn").click();
            cy.get(".fides-modal-content").should("be.visible");
            cy.get(".fides-modal-overlay").click({ force: true });
            cy.get(".fides-modal-content").should("not.be.visible");

            assertDismissCalled();
          });

          it("should dismiss the modal by hitting ESC", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.getByTestId("Manage preferences-btn").click();
            cy.get(".fides-modal-content").should("be.visible");
            cy.get("body").type("{esc}");
            cy.get(".fides-modal-content").should("not.be.visible");

            assertDismissCalled();
          });
        });
      } else {
        /**
         * Tests for the special case, when dismissal is prevented
         */
        describe("when using the banner", () => {
          it("should not show the x button", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.get("#fides-banner").within(() => {
              cy.get(".fides-close-button").should("not.be.visible");
            });

            cy.get("@FidesUpdated").should("not.have.been.called");
          });

          it("should not dismiss the banner by clicking outside", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.get("h1").click({ force: true }); // click outside
            cy.get("#fides-banner").should("be.visible");

            cy.get("@FidesUpdated").should("not.have.been.called");
          });

          it("should not dismiss the banner by hitting ESC", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.get("body").type("{esc}");
            cy.get("#fides-banner").should("be.visible");

            cy.get("@FidesUpdated").should("not.have.been.called");
          });
        });

        describe("when using the modal", () => {
          it("should not show the x button", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.getByTestId("Manage preferences-btn").click();
            cy.get(".fides-modal-content").should("be.visible");
            cy.get(".fides-modal-content").within(() => {
              cy.get(".fides-close-button").should("not.be.visible");
            });

            cy.get("@FidesUpdated").should("not.have.been.called");
          });

          it("should not dismiss the modal by clicking outside", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.getByTestId("Manage preferences-btn").click();
            cy.get(".fides-modal-content").should("be.visible");
            cy.get(".fides-modal-overlay").click({ force: true });
            cy.get(".fides-modal-content").should("be.visible");

            cy.get("@FidesUpdated").should("not.have.been.called");
          });

          it("should not dismiss the modal by hitting ESC", () => {
            cy.get("#fides-banner").should("be.visible");
            cy.getByTestId("Manage preferences-btn").click();
            cy.get(".fides-modal-content").should("be.visible");
            cy.get("body").type("{esc}");
            cy.get(".fides-modal-content").should("be.visible");

            cy.get("@FidesUpdated").should("not.have.been.called");
          });
        });
      }
    });
  });
});
