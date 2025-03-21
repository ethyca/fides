import { CONSENT_COOKIE_NAME } from "fides-js";
import { stubConfig } from "support/stubs";

const PRIVACY_NOTICE_KEY_1 = "advertising";
const PRIVACY_NOTICE_KEY_2 = "essential";
const PRIVACY_NOTICE_KEY_3 = "analytics_opt_out";

describe("Consent third party extensions", () => {
  describe("Meta Pixel integration", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
      });
    });
    it("sets the fbq.queue variable", () => {
      cy.window().then((win) => {
        // Meta Pixel configuration
        expect(win)
          .to.have.nested.property("fbq.queue")
          .that.eql([
            ["consent", "revoke"],
            ["dataProcessingOptions", ["LDU"], 1, 1000],
          ]);
      });
    });
  });

  describe("GTM integration", () => {
    describe("GTM default", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });
        cy.get("@FidesInitializing").should("have.been.calledOnce");
      });
      it("sets the dataLayer variable", () => {
        cy.window().then((win) => {
          expect(win).to.have.nested.property("dataLayer").to.exist;
        });
      });
      it("pushes Fides events to the GTM integration", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("@FidesUIShown").then(() => {
            cy.contains("button", "Opt in to all").should("be.visible").click();
            cy.get("@dataLayerPush")
              .should("have.been.callCount", 4) // FidesInitialized + FidesUIShown + FidesUpdating + FidesUpdated
              // First call should be from initialization, before the user accepts all
              .its("firstCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesInitialized",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: false,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                  },
                  extraDetails: {
                    consentMethod: undefined,
                    shouldShowExperience: true,
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Second call is FidesUIShown when banner appears
              .its("secondCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesUIShown",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: false,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                  },
                  extraDetails: {
                    servingComponent: "banner",
                    consentMethod: undefined,
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Third call is when the user accepts all
              .its("thirdCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesUpdating",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: true,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                  },
                  extraDetails: {
                    consentMethod: "accept",
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Fourth call is when the preferences finish updating
              .its("lastCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesUpdated",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: true,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                  },
                  extraDetails: {
                    consentMethod: "accept",
                  },
                  fides_string: undefined,
                },
              });
          });
        });
      });
    });

    describe("GTM with `asStringValues` enabled", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
            },
          },
          undefined,
          undefined,
          undefined,
          {
            gtmOptions: {
              asStringValues: true,
            },
          },
        );
        cy.get("@FidesInitializing").should("have.been.calledOnce");
      });
      it("converts consent to string values", () => {
        cy.get("@FidesInitializing").should("have.been.calledOnce");

        cy.waitUntilFidesInitialized().then(() => {
          cy.get("@FidesUIShown").then(() => {
            cy.contains("button", "Opt in to all").should("be.visible").click();
            cy.get("@dataLayerPush")
              .should("have.been.callCount", 4) // FidesInitialized + FidesUIShown + FidesUpdating + FidesUpdated
              // First call should be from initialization, before the user accepts all
              .its("firstCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesInitialized",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: "opt_out",
                    [PRIVACY_NOTICE_KEY_2]: "acknowledge",
                    [PRIVACY_NOTICE_KEY_3]: "opt_in",
                  },
                  extraDetails: {
                    consentMethod: undefined,
                    shouldShowExperience: true,
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Second call is FidesUIShown when banner appears
              .its("secondCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesUIShown",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: "opt_out",
                    [PRIVACY_NOTICE_KEY_2]: "acknowledge",
                    [PRIVACY_NOTICE_KEY_3]: "opt_in",
                  },
                  extraDetails: {
                    servingComponent: "banner",
                    consentMethod: undefined,
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Third call is when the user accepts all
              .its("thirdCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesUpdating",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: "opt_in",
                    [PRIVACY_NOTICE_KEY_2]: "acknowledge",
                    [PRIVACY_NOTICE_KEY_3]: "opt_in",
                  },
                  extraDetails: {
                    consentMethod: "accept",
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Fourth call is when the preferences finish updating
              .its("lastCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesUpdated",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: "opt_in",
                    [PRIVACY_NOTICE_KEY_2]: "acknowledge",
                    [PRIVACY_NOTICE_KEY_3]: "opt_in",
                  },
                  extraDetails: {
                    consentMethod: "accept",
                  },
                  fides_string: undefined,
                },
              });
          });
        });
      });
    });

    describe("GTM with `includeNotApplicable` enabled", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig(
          {
            experience: {
              non_applicable_privacy_notices: ["na_notice_1", "na_notice_2"],
            },
            options: {
              isOverlayEnabled: true,
            },
          },
          undefined,
          undefined,
          undefined,
          {
            gtmOptions: {
              includeNotApplicable: true,
            },
          },
        );
        cy.get("@FidesInitializing").should("have.been.calledOnce");
      });
      it("includes non-applicable privacy notices in the dataLayer", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("@FidesUIShown").then(() => {
            cy.contains("button", "Opt in to all").should("be.visible").click();
            cy.get("@dataLayerPush")
              .should("have.been.callCount", 4) // FidesInitialized + FidesUIShown + FidesUpdating + FidesUpdated
              // First call should be from initialization, before the user accepts all
              .its("firstCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesInitialized",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: false,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                    na_notice_1: true,
                    na_notice_2: true,
                  },
                  extraDetails: {
                    consentMethod: undefined,
                    shouldShowExperience: true,
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Second call is FidesUIShown when banner appears
              .its("secondCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesUIShown",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: false,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                    na_notice_1: true,
                    na_notice_2: true,
                  },
                  extraDetails: {
                    servingComponent: "banner",
                    consentMethod: undefined,
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Third call is when the user accepts all
              .its("thirdCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesUpdating",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: true,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                    na_notice_1: true,
                    na_notice_2: true,
                  },
                  extraDetails: {
                    consentMethod: "accept",
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Fourth call is when the preferences finish updating
              .its("lastCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesUpdated",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: true,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                    na_notice_1: true,
                    na_notice_2: true,
                  },
                  extraDetails: {
                    consentMethod: "accept",
                  },
                  fides_string: undefined,
                },
              });
          });
        });
      });
    });
  });
});
