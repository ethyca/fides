import { CONSENT_COOKIE_NAME, ConsentMethod, FidesCookie } from "fides-js";

import { stubConfig, stubTCFExperience } from "../support/stubs";

describe("Banner and modal dismissal", () => {
  // Helper function for some test case assertions
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
          decodeURIComponent(cookie!.value),
        );
        expect(fidesCookie.fides_meta)
          .property("consentMethod")
          .is.eql(ConsentMethod.DISMISS);
      });
    });

    cy.wait("@patchPrivacyPreference");
  }
  enum Expectation {
    DISMISSABLE,
    NOT_DISMISSABLE,
  }

  // Test all combinations of TCF enabled/disabled and prevent dismissal enabled/disabled
  interface TestCaseOptions {
    tcfEnabled: boolean;
    // this comes from the env var "PREVENT_DISMISSAL", and should take precedence over the below
    preventDismissal: boolean;
    // this comes from the experience config
    dismissable: boolean;
    expectation: Expectation;
  }

  const testCases: TestCaseOptions[] = [
    {
      tcfEnabled: false,
      preventDismissal: false,
      dismissable: true,
      expectation: Expectation.DISMISSABLE,
    },
    {
      tcfEnabled: false,
      preventDismissal: true,
      dismissable: true,
      expectation: Expectation.NOT_DISMISSABLE,
    },
    {
      tcfEnabled: false,
      preventDismissal: false,
      dismissable: false,
      expectation: Expectation.NOT_DISMISSABLE,
    },
    {
      tcfEnabled: false,
      preventDismissal: true,
      dismissable: false,
      expectation: Expectation.NOT_DISMISSABLE,
    },
    {
      tcfEnabled: true,
      preventDismissal: false,
      dismissable: true,
      expectation: Expectation.DISMISSABLE,
    },
    {
      tcfEnabled: true,
      preventDismissal: true,
      dismissable: true,
      expectation: Expectation.NOT_DISMISSABLE,
    },
    {
      tcfEnabled: true,
      preventDismissal: false,
      dismissable: false,
      expectation: Expectation.NOT_DISMISSABLE,
    },
    {
      tcfEnabled: true,
      preventDismissal: true,
      dismissable: false,
      expectation: Expectation.NOT_DISMISSABLE,
    },
  ];

  testCases.forEach(
    ({ tcfEnabled, preventDismissal, dismissable, expectation }) => {
      describe(`when tcfEnabled is ${tcfEnabled} and preventDismissal is ${preventDismissal} and dismissable is ${dismissable}`, () => {
        beforeEach(() => {
          if (!tcfEnabled) {
            cy.fixture("consent/fidesjs_options_banner_modal.json").then(
              (config) => {
                const experienceItem = config.experience;
                experienceItem.experience_config.dismissable = dismissable;
                stubConfig({
                  options: { tcfEnabled, preventDismissal },
                  experience: experienceItem,
                });
              },
            );
          } else {
            stubTCFExperience({
              stubOptions: { tcfEnabled, preventDismissal },
              experienceConfig: { dismissable },
            });
          }
        });

        if (expectation === Expectation.DISMISSABLE) {
          /**
           * Tests for when dismissal is allowed
           */
          describe("when using the banner", () => {
            it("should dismiss the banner by clicking the x", () => {
              cy.get("#fides-banner").should("be.visible");
              cy.get("#fides-banner .fides-close-button").click();
              cy.get("@FidesUpdated").should("have.been.called");
              cy.get("#fides-banner").should("not.be.visible");
              assertDismissCalled();
            });

            it("should not dismiss the banner by clicking outside", () => {
              cy.get("#fides-banner").should("be.visible");
              cy.get("h1").first().click(); // click outside
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
            it("should dismiss the modal by clicking the x", () => {
              cy.get("#fides-banner").should("be.visible");
              cy.getByTestId("Manage preferences-btn").click();
              cy.get(".fides-modal-content").should("be.visible");
              cy.get(".fides-modal-content .fides-close-button").click();
              cy.get(".fides-modal-content").should("not.be.visible");
              assertDismissCalled();
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
        } else {
          /**
           * Tests for the special case, when dismissal is prevented
           */
          describe("when using the banner", () => {
            it("should not show the x button", () => {
              cy.get("#fides-banner").should("be.visible");
              cy.get("#fides-banner .fides-close-button").should(
                "not.be.visible",
              );
              cy.get("@FidesUpdated").should("not.have.been.called");
            });

            it("should not dismiss the banner by clicking outside", () => {
              cy.get("#fides-banner").should("be.visible");
              cy.get("h1").first().click({ force: true }); // click outside
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
              cy.get(".fides-modal-content .fides-close-button").should(
                "not.be.visible",
              );
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
    },
  );
});
