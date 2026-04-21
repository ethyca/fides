import {
  CONSENT_COOKIE_NAME,
  ConsentFlagType,
  ConsentNonApplicableFlagMode,
} from "fides-js";
import { stubConfig, stubTCFExperience } from "support/stubs";

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
    const isTCFExperience = [false, true];
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
            cy.get("div#fides-banner").within(() => {
              cy.contains("button", "Opt in to all")
                .should("be.visible")
                .click();
            });
            cy.get("@dataLayerPush")
              .should("have.been.callCount", 5) // FidesReady + FidesInitialized + FidesUIShown + FidesUpdating + FidesUpdated
              // First call should be from initialization ready, before the user accepts all
              .its("firstCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesReady",
                Fides: {
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: false,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                  },
                  extraDetails: {
                    consentMethod: undefined,
                    shouldShowExperience: true,
                    trigger: {
                      origin: "fides",
                    },
                  },
                  fides_string: undefined,
                },
              });
            // Second call should be from FidesInitialized (dispatched at FidesReady time for backwards compatibility)
            cy.get("@dataLayerPush")
              .its("args")
              .then((args) => {
                const call = args[1][0];
                expect(call.event).to.equal("FidesInitialized");
                expect(call.Fides).to.deep.include({
                  consent: {
                    [PRIVACY_NOTICE_KEY_1]: false,
                    [PRIVACY_NOTICE_KEY_2]: true,
                    [PRIVACY_NOTICE_KEY_3]: true,
                  },
                  extraDetails: {
                    consentMethod: undefined,
                    shouldShowExperience: true,
                    trigger: {
                      origin: "fides",
                    },
                  },
                  fides_string: undefined,
                });
              });
            cy.get("@dataLayerPush")
              // Third call is FidesUIShown when banner appears
              .its("thirdCall.args.0")
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
                    trigger: {
                      origin: "fides",
                    },
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Fourth call is when the user accepts all
              .its("args")
              .then((args) => args[3][0])
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
                    servingComponent: "banner",
                    trigger: {
                      origin: "fides",
                      type: "button",
                      label: "Opt in to all",
                    },
                  },
                  fides_string: undefined,
                },
              });
            cy.get("@dataLayerPush")
              // Fifth call is when the preferences finish updating
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
                    servingComponent: "banner",
                    trigger: {
                      origin: "fides",
                      type: "button",
                      label: "Opt in to all",
                    },
                  },
                  fides_string: undefined,
                },
              });
          });
        });
      });
    });

    isTCFExperience.forEach((isTCF) => {
      describe(`GTM with ${isTCF ? "TCF" : "non-TCF"} experience and \`flag_type\` set to "consent_mechanism"`, () => {
        beforeEach(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          if (isTCF) {
            stubTCFExperience({
              includeCustomPurposes: true,
              demoPageWindowParams: {
                gtmOptions: {
                  flag_type: ConsentFlagType.CONSENT_MECHANISM,
                },
              },
            });
          } else {
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
                  flag_type: ConsentFlagType.CONSENT_MECHANISM,
                },
              },
            );
          }
          cy.get("@FidesInitializing").should("have.been.calledOnce");
        });
        it("converts consent to string values", () => {
          cy.get("@FidesInitializing").should("have.been.calledOnce");

          cy.waitUntilFidesInitialized().then(() => {
            cy.get("@FidesUIShown").then(() => {
              cy.get("div#fides-banner").within(() => {
                cy.contains("button", "Opt in to all")
                  .should("be.visible")
                  .click();
              });
              cy.get("@dataLayerPush").should("have.been.callCount", 5); // FidesReady + FidesInitialized + FidesUIShown + FidesUpdating + FidesUpdated

              // First call should be from initialization, before the user accepts all
              cy.get("@dataLayerPush")
                .its("firstCall.args.0.event")
                .should("eq", "FidesReady");
              cy.get("@dataLayerPush")
                .its("firstCall.args.0.Fides.consent")
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: "opt_out",
                  [PRIVACY_NOTICE_KEY_2]: "acknowledge",
                  [PRIVACY_NOTICE_KEY_3]: "opt_in",
                });
              cy.get("@dataLayerPush")
                .its("firstCall.args.0.Fides.extraDetails")
                .should("deep.equal", {
                  consentMethod: undefined,
                  shouldShowExperience: true,
                  trigger: {
                    origin: "fides",
                  },
                });
              // Second call should be from FidesInitialized (dispatched at FidesReady time for backwards compatibility)
              cy.get("@dataLayerPush")
                .its("secondCall.args.0.event")
                .should("eq", "FidesInitialized");
              cy.get("@dataLayerPush")
                .its("secondCall.args.0.Fides.consent")
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: "opt_out",
                  [PRIVACY_NOTICE_KEY_2]: "acknowledge",
                  [PRIVACY_NOTICE_KEY_3]: "opt_in",
                });
              cy.get("@dataLayerPush")
                .its("secondCall.args.0.Fides.extraDetails")
                .should("deep.equal", {
                  consentMethod: undefined,
                  shouldShowExperience: true,
                  trigger: {
                    origin: "fides",
                  },
                });

              // Third call is FidesUIShown when banner appears
              cy.get("@dataLayerPush")
                .its("thirdCall.args.0.event")
                .should("eq", "FidesUIShown");
              cy.get("@dataLayerPush")
                .its("thirdCall.args.0.Fides.consent")
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: "opt_out",
                  [PRIVACY_NOTICE_KEY_2]: "acknowledge",
                  [PRIVACY_NOTICE_KEY_3]: "opt_in",
                });
              cy.get("@dataLayerPush")
                .its("thirdCall.args.0.Fides.extraDetails")
                .should("deep.equal", {
                  servingComponent: isTCF ? "tcf_banner" : "banner",
                  consentMethod: undefined,
                  trigger: {
                    origin: "fides",
                  },
                });

              // Fourth call is when the user accepts all
              cy.get("@dataLayerPush")
                .its("args")
                .then((args) => args[3][0].event)
                .should("eq", "FidesUpdating");
              cy.get("@dataLayerPush")
                .its("args")
                .then((args) => args[3][0].Fides.consent)
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: "opt_in",
                  [PRIVACY_NOTICE_KEY_2]: "acknowledge",
                  [PRIVACY_NOTICE_KEY_3]: "opt_in",
                });
              cy.get("@dataLayerPush")
                .its("args")
                .then((args) => args[3][0].Fides.extraDetails)
                .should("deep.equal", {
                  consentMethod: "accept",
                  servingComponent: isTCF ? "tcf_banner" : "banner",
                  trigger: {
                    origin: "fides",
                    type: "button",
                    label: "Opt in to all",
                  },
                });

              // Last call is when the preferences finish updating
              cy.get("@dataLayerPush")
                .its("lastCall.args.0.event")
                .should("eq", "FidesUpdated");
              cy.get("@dataLayerPush")
                .its("lastCall.args.0.Fides.consent")
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: "opt_in",
                  [PRIVACY_NOTICE_KEY_2]: "acknowledge",
                  [PRIVACY_NOTICE_KEY_3]: "opt_in",
                });
              cy.get("@dataLayerPush")
                .its("lastCall.args.0.Fides.extraDetails")
                .should("deep.equal", {
                  consentMethod: "accept",
                  servingComponent: isTCF ? "tcf_banner" : "banner",
                  trigger: {
                    origin: "fides",
                    type: "button",
                    label: "Opt in to all",
                  },
                });
            });
          });
        });
      });
    });

    isTCFExperience.forEach((isTCF) => {
      describe(`GTM with ${isTCF ? "TCF" : "non-TCF"} experience and \`non_applicable_flag_mode\` set to "include"`, () => {
        beforeEach(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          if (isTCF) {
            stubTCFExperience({
              includeCustomPurposes: true,
              experienceMinimalOverride: {
                non_applicable_privacy_notices: ["na_notice_1", "na_notice_2"],
              },
              demoPageWindowParams: {
                gtmOptions: {
                  non_applicable_flag_mode:
                    ConsentNonApplicableFlagMode.INCLUDE,
                },
              },
            });
          } else {
            stubConfig(
              {
                experience: {
                  non_applicable_privacy_notices: [
                    "na_notice_1",
                    "na_notice_2",
                  ],
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
                  non_applicable_flag_mode:
                    ConsentNonApplicableFlagMode.INCLUDE,
                },
              },
            );
          }
          cy.get("@FidesInitializing").should("have.been.calledOnce");
        });
        it("includes non-applicable privacy notices in the dataLayer", () => {
          cy.waitUntilFidesInitialized().then(() => {
            cy.get("@FidesUIShown").then(() => {
              cy.get("div#fides-banner").within(() => {
                cy.contains("button", "Opt in to all")
                  .should("be.visible")
                  .click();
              });
              cy.get("@dataLayerPush").should("have.been.callCount", 5); // FidesReady + FidesInitialized + FidesUIShown + FidesUpdating + FidesUpdated

              // First call should be from initialization, before the user accepts all
              cy.get("@dataLayerPush")
                .its("firstCall.args.0.event")
                .should("eq", "FidesReady");
              cy.get("@dataLayerPush")
                .its("firstCall.args.0.Fides.consent")
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: false,
                  [PRIVACY_NOTICE_KEY_2]: true,
                  [PRIVACY_NOTICE_KEY_3]: true,
                  na_notice_1: true,
                  na_notice_2: true,
                });
              cy.get("@dataLayerPush")
                .its("firstCall.args.0.Fides.extraDetails")
                .should("deep.equal", {
                  consentMethod: undefined,
                  shouldShowExperience: true,
                  trigger: {
                    origin: "fides",
                  },
                });

              // Second call should be from FidesInitialized (dispatched at FidesReady time for backwards compatibility)
              cy.get("@dataLayerPush")
                .its("secondCall.args.0.event")
                .should("eq", "FidesInitialized");
              cy.get("@dataLayerPush")
                .its("secondCall.args.0.Fides.consent")
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: false,
                  [PRIVACY_NOTICE_KEY_2]: true,
                  [PRIVACY_NOTICE_KEY_3]: true,
                  na_notice_1: true,
                  na_notice_2: true,
                });
              cy.get("@dataLayerPush")
                .its("secondCall.args.0.Fides.extraDetails")
                .should("deep.equal", {
                  consentMethod: undefined,
                  shouldShowExperience: true,
                  trigger: {
                    origin: "fides",
                  },
                });

              // Third call is FidesUIShown when banner appears
              cy.get("@dataLayerPush")
                .its("thirdCall.args.0.event")
                .should("eq", "FidesUIShown");
              cy.get("@dataLayerPush")
                .its("thirdCall.args.0.Fides.consent")
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: false,
                  [PRIVACY_NOTICE_KEY_2]: true,
                  [PRIVACY_NOTICE_KEY_3]: true,
                  na_notice_1: true,
                  na_notice_2: true,
                });
              cy.get("@dataLayerPush")
                .its("thirdCall.args.0.Fides.extraDetails")
                .should("deep.equal", {
                  servingComponent: isTCF ? "tcf_banner" : "banner",
                  consentMethod: undefined,
                  trigger: {
                    origin: "fides",
                  },
                });

              // Fourth call is when the user accepts all
              cy.get("@dataLayerPush")
                .its("args")
                .then((args) => args[3][0].event)
                .should("eq", "FidesUpdating");
              cy.get("@dataLayerPush")
                .its("args")
                .then((args) => args[3][0].Fides.consent)
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: true,
                  [PRIVACY_NOTICE_KEY_2]: true,
                  [PRIVACY_NOTICE_KEY_3]: true,
                  na_notice_1: true,
                  na_notice_2: true,
                });
              cy.get("@dataLayerPush")
                .its("args")
                .then((args) => args[3][0].Fides.extraDetails)
                .should("deep.equal", {
                  consentMethod: "accept",
                  servingComponent: isTCF ? "tcf_banner" : "banner",
                  trigger: {
                    origin: "fides",
                    type: "button",
                    label: "Opt in to all",
                  },
                });

              // Last call is when the preferences finish updating
              cy.get("@dataLayerPush")
                .its("lastCall.args.0.event")
                .should("eq", "FidesUpdated");
              cy.get("@dataLayerPush")
                .its("lastCall.args.0.Fides.consent")
                .should("deep.equal", {
                  [PRIVACY_NOTICE_KEY_1]: true,
                  [PRIVACY_NOTICE_KEY_2]: true,
                  [PRIVACY_NOTICE_KEY_3]: true,
                  na_notice_1: true,
                  na_notice_2: true,
                });
              cy.get("@dataLayerPush")
                .its("lastCall.args.0.Fides.extraDetails")
                .should("deep.equal", {
                  consentMethod: "accept",
                  servingComponent: isTCF ? "tcf_banner" : "banner",
                  trigger: {
                    origin: "fides",
                    type: "button",
                    label: "Opt in to all",
                  },
                });
            });
          });
        });
      });
    });
  });

  describe("Matomo integration", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
      });
      cy.get("@FidesInitializing").should("have.been.calledOnce");
    });

    it("pushes requireConsent on FidesReady when analytics key is present", () => {
      cy.waitUntilFidesInitialized().then(() => {
        // The fixture has analytics_opt_out (not analytics), so Matomo should
        // NOT have pushed requireConsent since neither "analytics" nor
        // "performance" keys are present.
        cy.get("@paqPush").should("not.have.been.called");
      });
    });

    it("pushes consent commands when the analytics notice key is present", () => {
      // Override the stub to use a config with an "analytics" notice key
      stubConfig(
        {
          experience: {
            privacy_notices: [
              {
                id: "pri_analytics",
                origin: "pri_xxx",
                created_at: "2024-01-01T12:00:00.000000+00:00",
                updated_at: "2024-01-01T12:00:00.000000+00:00",
                name: "Analytics",
                notice_key: "analytics",
                consent_mechanism: "opt_in" as any,
                data_uses: ["analytics"],
                enforcement_level: "frontend" as any,
                disabled: false,
                has_gpc_flag: false,
                framework: null,
                default_preference: "opt_out" as any,
                cookies: [],
                systems_applicable: true,
                translations: [
                  {
                    language: "en",
                    title: "Analytics",
                    description: "We use analytics to improve our site.",
                    privacy_notice_history_id: "pri_analytics_history",
                  },
                ],
              },
            ],
          },
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        undefined,
        undefined,
      );
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").then(() => {
          // On FidesReady, analytics defaults to opt_out (false), so Matomo
          // should have pushed requireConsent + forgetConsentGiven
          cy.get("@paqPush").should("have.been.calledWith", ["requireConsent"]);
          cy.get("@paqPush").should("have.been.calledWith", [
            "forgetConsentGiven",
          ]);

          // Now opt in via the banner
          cy.get("div#fides-banner").within(() => {
            cy.contains("button", "Opt in to all").should("be.visible").click();
          });

          // After opting in, Matomo should receive rememberConsentGiven
          cy.get("@paqPush").should("have.been.calledWith", [
            "rememberConsentGiven",
          ]);
        });
      });
    });
  });
});
