/* eslint-disable no-underscore-dangle */
import { TCString } from "@iabtechlabtcf/core";
import {
  CONSENT_COOKIE_NAME,
  ConsentMethod,
  FidesCookie,
  FidesEndpointPaths,
  Layer1ButtonOption,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  RejectAllMechanism,
} from "fides-js";
import { NoticeConsent } from "fides-js/src/lib/consent-types";
import { FIDES_SEPARATOR } from "fides-js/src/lib/tcf/constants";

import {
  API_URL,
  TCF_VERSION_HASH,
  TEST_OVERRIDE_WINDOW_PATH,
} from "../support/constants";
import { mockCookie, mockTcfVendorObjects } from "../support/mocks";
import { OVERRIDE, stubConfig, stubTCFExperience } from "../support/stubs";

const PRIVACY_NOTICE_KEY_1 = "advertising";
const PRIVACY_NOTICE_KEY_2 = "essential";
const PRIVACY_NOTICE_KEY_3 = "analytics_opt_out";

const PURPOSE_2 = {
  id: 2,
  name: "Use limited data to select advertising",
};
const PURPOSE_4 = {
  id: 4,
  name: "Use profiles to select personalised advertising",
};
const PURPOSE_6 = {
  id: 6,
  name: "Use profiles to select personalised content",
};
const PURPOSE_7 = {
  id: 7,
  name: "Measure advertising performance",
};
const PURPOSE_9 = {
  id: 9,
  name: "Understand audiences through statistics or combinations of data from different sources",
};
const SPECIAL_PURPOSE_1 = {
  id: 1,
  name: "Ensure security, prevent and detect fraud, and fix errors",
};
const SYSTEM_1 = {
  id: "ctl_b3dde2d5-e535-4d9a-bf6e-a3b6beb01761",
  name: "Fides System",
};
const VENDOR_1 = {
  id: "gvl.2",
  name: "Captify",
};
const VENDOR_2 = {
  id: "gvl.3",
  name: "Fides System",
};
const STACK_1 = {
  id: 7,
  name: "Selection of personalised advertising, advertising measurement, and audience research",
};
const FEATURE_1 = {
  id: 1,
  name: "Match and combine data from other data sources",
};
const FEATURE_2 = {
  id: 2,
  name: "Link different devices",
};
const SPECIAL_FEATURE_1 = {
  id: 1,
  name: "Use precise geolocation data",
};

const checkDefaultExperienceRender = () => {
  // Purposes
  // Check consents first
  // todo- verify custom toggles
  cy.getByTestId(`toggle-${PURPOSE_4.name}`).within(() => {
    cy.get("input").should("not.be.checked");
  });
  cy.getByTestId(`toggle-${PURPOSE_9.name}`).within(() => {
    cy.get("input").should("not.be.checked");
  });
  cy.get(".fides-record-header").contains("Special purposes");
  cy.get(".fides-notice-toggle-title").contains(SPECIAL_PURPOSE_1.name);
  cy.getByTestId(`toggle-${SPECIAL_PURPOSE_1.name}`).should("not.exist");
  // Check legints
  cy.get("button").contains("Legitimate interest").click();
  cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
    cy.get("input").should("be.checked");
  });

  cy.get("#fides-tab-features").click();
  cy.get(".fides-record-header").contains("Features");
  cy.get(".fides-notice-toggle-title").contains(FEATURE_1.name);
  cy.get(".fides-notice-toggle-title").contains(FEATURE_2.name);
  cy.getByTestId(`toggle-${FEATURE_1.name}`).should("not.exist");
  cy.getByTestId(`toggle-${FEATURE_2.name}`).should("not.exist");
  cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
    cy.get("input").should("not.be.checked");
  });

  // Vendors
  cy.get("#fides-tab-vendors").click();
  cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
    cy.get("input").should("not.be.checked");
  });
  cy.get("#fides-panel-vendors").within(() => {
    cy.get("button").contains("Legitimate interest").click();
    cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
      cy.get("input").should("be.checked");
    });
  });
};

const assertTcOptIns = ({
  cookie,
  modelType,
  ids,
}: {
  cookie: FidesCookie;
  modelType:
    | "purposeConsents"
    | "purposeLegitimateInterests"
    | "specialFeatureOptins"
    | "vendorConsents"
    | "vendorLegitimateInterests";
  ids: number[];
}) => {
  const { fides_string: fidesString } = cookie;
  const tcString = fidesString?.split(FIDES_SEPARATOR)[0];
  expect(tcString).to.be.a("string");
  expect(tcString).to.not.equal("");
  const model = TCString.decode(tcString);
  const values = Array.from(model[modelType].values()).sort();
  expect(values).to.eql(ids.sort());
};

const assertAcOptIns = ({
  cookie,
  ids,
}: {
  cookie: FidesCookie;
  ids: number[];
}) => {
  const { fides_string: fidesString } = cookie;
  const acString = fidesString?.split(",")[1];
  expect(acString).to.be.a("string");
  const acConsent = acString.split("~")[1];
  const values = acConsent
    .split(".")
    .map((id) => +id)
    .sort();
  expect(values).to.eql(ids.sort());
};

const fidesVendorIdToId = (fidesId: string) => +fidesId.split(".")[1];

const testCustomPurposes = [false, true];

describe("Fides-js TCF", () => {
  beforeEach(() => {
    cy.intercept("GET", `${API_URL}${FidesEndpointPaths.GVL_TRANSLATIONS}*`, {
      fixture: "consent/gvl_translations.json",
    }).as("getGvlTranslations");
  });
  describe("banner appears when it should", () => {
    beforeEach(() => {
      cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
        fixture: "consent/notices_served_tcf.json",
      }).as("patchNoticesServed");
    });

    it("should render the banner if there is no saved version hash", () => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubTCFExperience({});
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, ({ eventStatus }) => {
          if (eventStatus) {
            expect(eventStatus).to.eql("tcloaded");
          }
        });
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        cy.get("div#fides-banner").should("be.visible");
      });
    });

    it("should render the banner if the saved hash does not match", () => {
      const cookie = mockCookie({
        tcf_version_hash: "ec87e92ce5bc",
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      stubTCFExperience({});
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, ({ eventStatus }) => {
          if (eventStatus) {
            expect(eventStatus).to.eql("cmpuishown");
          }
        });
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        cy.get("div#fides-banner").should("be.visible");
      });
    });

    it("should not render the banner if the saved hashes match", () => {
      const cookie = mockCookie({
        tcf_version_hash: TCF_VERSION_HASH,
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      stubTCFExperience({});
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, ({ eventStatus }) => {
          if (eventStatus) {
            expect(eventStatus).to.eql("tcloaded");
          }
        });
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("not.have.been.called");
        cy.get("div#fides-banner").should("not.exist");
      });
    });
    it("should not render the banner if fides_disable_banner is true", () => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");

      stubTCFExperience({ stubOptions: { fidesDisableBanner: true } });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("not.have.been.called");
        cy.get("div#fides-banner").should("not.exist");
      });
    });
  });

  describe("Payload optimization", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubTCFExperience({});
    });
    it("merges full experience with minimal after successful fetch", () => {
      cy.window().then((win) => {
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          cy.wait("@getPrivacyExperience");
          expect(
            (win.Fides.experience as PrivacyExperienceMinimal)
              .tcf_purpose_consent_ids,
          ).to.have.length(11);
          expect((win.Fides.experience as any).tcf_purpose_consents).to.not
            .exist;
          cy.waitUntilFidesInitialized().then(() => {
            const experience = payload.items[0];
            const updatedExperience = {
              ...experience,
              tcf_purpose_consents: [],
            };
            stubTCFExperience({
              experienceFullOverride: updatedExperience,
              skipVisit: true,
            });
            cy.waitUntil(() => {
              return (
                (win.Fides.experience as PrivacyExperience).tcf_purpose_consents
                  .length > 0
              );
            }).then(() => {
              expect(
                (
                  win.Fides.experience as PrivacyExperience &
                    PrivacyExperienceMinimal
                ).tcf_purpose_consent_ids,
              ).to.have.length(11);
              expect(
                (
                  win.Fides.experience as PrivacyExperience &
                    PrivacyExperienceMinimal
                ).tcf_purpose_consents,
              ).to.have.length(4);
            });
          });
        });
      });
    });
  });

  testCustomPurposes.forEach((includeCustomPurposes) => {
    describe(`initial layer ${includeCustomPurposes ? `with` : `without`} custom purposes`, () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubTCFExperience({ includeCustomPurposes });
        cy.intercept(
          "PATCH",
          `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`,
          {
            fixture: "consent/notices_served_tcf.json",
          },
        ).as("patchNoticesServed");
      });

      it("can render purposes in the initial layer", () => {
        cy.get("div#fides-banner").within(() => {
          if (includeCustomPurposes) {
            cy.contains("Advertising English");
          }
          cy.contains(PURPOSE_2.name);
          cy.contains(PURPOSE_6.name);
        });
      });

      it("can open the modal from vendor count", () => {
        cy.get("div#fides-banner").within(() => {
          cy.get(".fides-vendor-count")
            .first()
            .should("have.text", "16")
            .click();
        });
        cy.get("#fides-tab-vendors");
      });

      it("can open the modal from preferences button", () => {
        cy.get("div#fides-banner").within(() => {
          cy.get("#fides-button-group").within(() => {
            cy.get("button").contains("Manage preferences").click();
          });
        });
        cy.get("#fides-tab-purposes");
      });

      it("hides reject button based on configuration", () => {
        cy.get("div#fides-banner").within(() => {
          cy.get("#fides-button-group").within(() => {
            cy.get("button").contains("Opt out of all").should("be.visible");
          });
        });
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubTCFExperience({
          includeCustomPurposes,
          experienceConfig: {
            layer1_button_options: Layer1ButtonOption.OPT_IN_ONLY,
          },
        });
        cy.get("div#fides-banner").within(() => {
          cy.get("#fides-button-group").within(() => {
            cy.get("button").contains("Opt out of all").should("not.exist");
          });
        });
      });

      describe("saving preferences", () => {
        const vendorsDisclosed = ".IABE";
        it("can opt in to all", () => {
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          cy.get("div#fides-banner").within(() => {
            cy.get("button").contains("Opt in to all").click();
            cy.wait("@patchPrivacyPreference").then((interception) => {
              cy.get("@FidesUIChanged").should("not.have.been.called");
              const { body } = interception.request;
              expect(body.method).to.eql(ConsentMethod.ACCEPT);
              expect(body.purpose_consent_preferences).to.eql([
                {
                  id: PURPOSE_4.id,
                  preference: "opt_in",
                },
                {
                  id: PURPOSE_6.id,
                  preference: "opt_in",
                },
                {
                  id: PURPOSE_7.id,
                  preference: "opt_in",
                },
                {
                  id: PURPOSE_9.id,
                  preference: "opt_in",
                },
              ]);
              expect(body.purpose_legitimate_interests_preferences).to.eql([
                {
                  id: PURPOSE_2.id,
                  preference: "opt_in",
                },
              ]);
              expect(body.special_purpose_preferences).to.eql(undefined);
              expect(body.feature_preferences).to.eql(undefined);
              expect(body.special_feature_preferences).to.eql([
                {
                  id: SPECIAL_FEATURE_1.id,
                  preference: "opt_in",
                },
              ]);
              expect(body.vendor_consent_preferences).to.eql([
                {
                  id: VENDOR_1.id,
                  preference: "opt_in",
                },
              ]);
              expect(body.vendor_legitimate_interests_preferences).to.eql([]);
              expect(body.system_legitimate_interests_preferences).to.eql([
                {
                  id: SYSTEM_1.id,
                  preference: "opt_in",
                },
              ]);
              expect(body.system_consent_preferences).to.eql([]);
            });
          });
          // Verify the cookie on save
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
              ConsentMethod.ACCEPT,
            );
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "purposeConsents",
              ids: [PURPOSE_9.id, PURPOSE_6.id, PURPOSE_7.id, PURPOSE_4.id],
            });
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "purposeLegitimateInterests",
              ids: [PURPOSE_2.id],
            });
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "specialFeatureOptins",
              ids: [SPECIAL_FEATURE_1.id],
            });
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "vendorConsents",
              ids: [fidesVendorIdToId(VENDOR_1.id)],
            });
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "vendorLegitimateInterests",
              ids: [fidesVendorIdToId(VENDOR_1.id)],
            });
            expect(
              cookieKeyConsent.tcf_consent.system_consent_preferences,
            ).to.eql({});
            expect(
              cookieKeyConsent.tcf_consent
                .system_legitimate_interests_preferences,
            )
              .property(`${SYSTEM_1.id}`)
              .is.eql(true);
            if (includeCustomPurposes) {
              // Confirm custom purposes are persisted to the cookie
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_1)
                .is.eql(true);
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_2)
                .is.eql(true);
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_3)
                .is.eql(true);
              expect(cookieKeyConsent.fides_meta)
                .property("consentMethod")
                .is.eql(ConsentMethod.ACCEPT);
            }

            // Confirm vendors_disclosed section does not exist
            expect(cookieKeyConsent.fides_string).to.not.contain(
              vendorsDisclosed,
            );
          });
          if (includeCustomPurposes) {
            // verify window object
            cy.window()
              .its("Fides")
              .its("consent")
              .should("eql", {
                [PRIVACY_NOTICE_KEY_1]: true,
                [PRIVACY_NOTICE_KEY_2]: true,
                [PRIVACY_NOTICE_KEY_3]: true,
              });
          }
          // verify the data layer variables
          cy.get("@dataLayerPush")
            .should("have.been.callCount", 5) // FidesReady + FidesInitialized + FidesUIShown (banner) + FidesUpdating + FidesUpdated
            // First call should be from initialization ready, before the user accepts all
            .its("firstCall.args.0")
            .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
            .should("deep.equal", {
              event: "FidesReady",
              Fides: {
                consent: includeCustomPurposes
                  ? {
                      advertising: false,
                      analytics_opt_out: true,
                      essential: true,
                    }
                  : {},
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
                consent: includeCustomPurposes
                  ? {
                      advertising: false,
                      analytics_opt_out: true,
                      essential: true,
                    }
                  : {},
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

          // Verify FidesUIShown events (banner and modal)
          cy.get("@dataLayerPush")
            .its("args")
            .then((args) => {
              // Banner shown event
              const bannerEvent = args[2][0];
              expect(bannerEvent.event).to.equal("FidesUIShown");
              expect(bannerEvent.Fides.extraDetails.servingComponent).to.equal(
                "tcf_banner",
              );

              // FidesUpdating event
              const updatingEvent = args[3][0];
              expect(updatingEvent.event).to.equal("FidesUpdating");
              expect(
                updatingEvent.Fides.extraDetails.servingComponent,
              ).to.equal("tcf_banner");

              // FidesUpdated event
              const updatedEvent = args[4][0];
              expect(updatedEvent.event).to.equal("FidesUpdated");
              expect(updatedEvent.Fides.extraDetails.servingComponent).to.equal(
                "tcf_banner",
              );
            });

          // FidesUpdating call
          cy.get("@dataLayerPush")
            .its("args")
            .then((args) => {
              const call = args[3][0];
              expect(call.event).to.equal("FidesUpdating");
              expect(call.Fides).to.deep.include({
                consent: includeCustomPurposes
                  ? {
                      advertising: true,
                      analytics_opt_out: true,
                      essential: true,
                    }
                  : {},
                extraDetails: {
                  consentMethod: "accept",
                  servingComponent: "tcf_banner",
                  trigger: {
                    type: "button",
                    label: "Opt in to all",
                    origin: "fides",
                  },
                },
              });
              expect(call.Fides.fides_string).to.contain(",2~~dv.");
            });

          // FidesUpdated call
          cy.get("@dataLayerPush")
            .its("args")
            .then((args) => {
              const call = args[4][0];
              expect(call.event).to.equal("FidesUpdated");
              expect(call.Fides).to.deep.include({
                consent: includeCustomPurposes
                  ? {
                      advertising: true,
                      analytics_opt_out: true,
                      essential: true,
                    }
                  : {},
                extraDetails: {
                  consentMethod: "accept",
                  servingComponent: "tcf_banner",
                  trigger: {
                    type: "button",
                    label: "Opt in to all",
                    origin: "fides",
                  },
                },
              });
              expect(call.Fides.fides_string).to.contain(",2~~dv.");
            });
        });

        it("can opt out of all", () => {
          cy.get("div#fides-banner").within(() => {
            cy.get("button").contains("Opt out of all").click();
            cy.wait("@patchPrivacyPreference").then((interception) => {
              cy.get("@FidesUIChanged").should("not.have.been.called");
              const { body } = interception.request;
              expect(interception.request.body.method).to.eql(
                ConsentMethod.REJECT,
              );
              expect(body.purpose_consent_preferences).to.eql([
                {
                  id: PURPOSE_4.id,
                  preference: "opt_out",
                },
                {
                  id: PURPOSE_6.id,
                  preference: "opt_out",
                },
                {
                  id: PURPOSE_7.id,
                  preference: "opt_out",
                },
                {
                  id: PURPOSE_9.id,
                  preference: "opt_out",
                },
              ]);
              expect(body.purpose_legitimate_interests_preferences).to.eql([
                {
                  id: PURPOSE_2.id,
                  preference: "opt_out",
                },
              ]);
              expect(body.special_purpose_preferences).to.eql(undefined);
              expect(body.feature_preferences).to.eql(undefined);
              expect(body.special_feature_preferences).to.eql([
                {
                  id: SPECIAL_FEATURE_1.id,
                  preference: "opt_out",
                },
              ]);
              expect(body.vendor_consent_preferences).to.eql([
                {
                  id: VENDOR_1.id,
                  preference: "opt_out",
                },
              ]);
              expect(body.vendor_legitimate_interests_preferences).to.eql([]);
              expect(body.system_legitimate_interests_preferences).to.eql([
                {
                  id: SYSTEM_1.id,
                  preference: "opt_out",
                },
              ]);
              expect(body.system_consent_preferences).to.eql([]);
            });
          });
          // Verify the cookie on save
          cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value),
              );
              expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
                ConsentMethod.REJECT,
              );
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeConsents",
                ids: [],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeLegitimateInterests",
                ids: [],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "specialFeatureOptins",
                ids: [],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorConsents",
                ids: [],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorLegitimateInterests",
                ids: [fidesVendorIdToId(VENDOR_1.id)],
              });
              expect(
                cookieKeyConsent.tcf_consent.system_consent_preferences,
              ).to.eql({});
              expect(
                cookieKeyConsent.tcf_consent
                  .system_legitimate_interests_preferences,
              )
                .property(`${SYSTEM_1.id}`)
                .is.eql(false);
              if (includeCustomPurposes) {
                // Confirm custom purposes are persisted to the cookie
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_1)
                  .is.eql(false);
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_2)
                  .is.eql(true);
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_3)
                  .is.eql(false);
                expect(cookieKeyConsent.fides_meta)
                  .property("consentMethod")
                  .is.eql(ConsentMethod.REJECT);
              }
              // Confirm vendors_disclosed section does not exist
              expect(cookieKeyConsent.fides_string).to.not.contain(
                vendorsDisclosed,
              );
            });
          });
        });

        it("can opt out of all with reject mechanism set to consent only", () => {
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          stubTCFExperience({
            includeCustomPurposes,
            experienceConfig: {
              reject_all_mechanism: RejectAllMechanism.REJECT_CONSENT_ONLY,
            },
          });
          cy.get("div#fides-banner").within(() => {
            cy.get("button").contains("Opt out of all").click();
            cy.wait("@patchPrivacyPreference").then((interception) => {
              cy.get("@FidesUIChanged").should("not.have.been.called");
              const { body } = interception.request;
              expect(interception.request.body.method).to.eql(
                ConsentMethod.REJECT,
              );
              expect(body.purpose_legitimate_interests_preferences).to.eql([
                {
                  id: PURPOSE_2.id,
                  preference: "opt_in",
                },
              ]);
            });
          });
          // Verify the cookie on save
          cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value),
              );
              expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
                ConsentMethod.REJECT,
              );
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeLegitimateInterests",
                ids: [2],
              });
            });
          });
        });
      });
    });
  });

  describe("second layer", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubTCFExperience({});
      cy.wait("@getPrivacyExperience");
      cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
        fixture: "consent/notices_served_tcf.json",
      }).as("patchNoticesServed");

      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });
    });

    describe("rendering the TCF modal", () => {
      it("can render tabs", () => {
        checkDefaultExperienceRender();
      });

      it("can render IAB TCF badge on vendors and split into their own lists", () => {
        const newVendor = {
          // Use the new vendor id scheme
          id: "gvl.1",
          name: "Exponential Interactive, Inc d/b/a VDX.tv",
        };
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience = payload.items[0];
          experience.tcf_vendor_consents.push(newVendor);
          experience.tcf_vendor_relationships.push(newVendor);
          stubTCFExperience({
            experienceFullOverride: experience,
          });
        });

        cy.get("div#fides-banner").within(() => {
          cy.get("#fides-button-group").within(() => {
            cy.get("button").contains("Manage preferences").click();
          });
        });

        cy.get("#fides-tab-vendors").click();
        cy.get("#fides-panel-vendors").within(() => {
          cy.getByTestId("records-list-vendors").within(() => {
            cy.get("span").contains(VENDOR_1.name);
            cy.get("span").contains("IAB TCF");
            cy.get("span").contains(newVendor.name);
            cy.get("span").contains("IAB TCF");
          });
          cy.get("span").contains(SYSTEM_1.name).should("not.exist");

          cy.get("button").contains("Legitimate interest").click();
          cy.getByTestId("records-list-vendors").within(() => {
            cy.get("span")
              .contains(SYSTEM_1.name)
              .within(() => {
                cy.get("span").should("not.exist");
              });
          });
        });

        // Check that the vendor ids persisted to the TC string
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        cy.get("@FidesUpdated")
          .should("have.been.calledOnce")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.ACCEPT);
          });
        cy.window().then((win) => {
          win.__tcfapi("getTCData", 2, cy.stub().as("getTCData"));
          cy.get("@getTCData")
            .should("have.been.calledOnce")
            .its("lastCall.args")
            .then(([tcData, success]) => {
              expect(success).to.eql(true);
              expect(tcData.vendor.consents).to.eql({ 1: true, 2: true });
            });
        });
      });

      it("can render extra vendor info such as cookie and retention data", () => {
        cy.get("#fides-tab-vendors").click();
        cy.get(".fides-notice-toggle-title").contains(VENDOR_1.name).click();
        cy.get(".fides-disclosure-visible").within(() => {
          // Check urls
          cy.get("a")
            .contains("Privacy policy")
            .should("have.attr", "href")
            .and("contain", "https://www.example.com/privacy");
          cy.get("a")
            .contains("Legitimate interest disclosure")
            .should("have.attr", "href")
            .and(
              "contain",
              "https://www.example.com/legitimate_interest_disclosure",
            );

          // Check retention periods
          [PURPOSE_4, PURPOSE_6, PURPOSE_7, PURPOSE_9].forEach((purpose) => {
            // In the fixture, all retention periods are their id's
            cy.get("tr")
              .contains(purpose.name)
              .parent()
              .contains(`${purpose.id} day(s)`);
          });
          cy.get("tr")
            .contains(SPECIAL_PURPOSE_1.name)
            .parent()
            .contains(`${SPECIAL_PURPOSE_1.id} day(s)`);

          // Check cookie disclosure
          cy.get("p").contains(
            'Captify stores cookies with a maximum duration of about this many days: 5. These cookies may be refreshed. This vendor also uses other methods like "local storage" to store and access information on your device.',
          );
        });
        // Check the cookie disclosure on the system
        // First close the vendor
        cy.get(".fides-notice-toggle-title").contains(VENDOR_1.name).click();
        // Then open the system
        cy.get("#fides-panel-vendors").within(() => {
          cy.get("button").contains("Legitimate interest").click();
        });
        cy.get(".fides-notice-toggle-title").contains(SYSTEM_1.name).click();
        cy.get(".fides-disclosure-visible").within(() => {
          cy.get("p").contains(
            "Fides System stores cookies with a maximum duration of about this many days: 5.",
          );
        });
      });

      it("can fire FidesUIChanged events", () => {
        // Enable the first purpose toggle
        cy.getByTestId(`toggle-${PURPOSE_4.name}`).click();
        cy.get("@FidesUIChanged").its("callCount").should("equal", 1);
        cy.get("@FidesUIChanged")
          .its("firstCall.args.0")
          .then((event: CustomEvent) => {
            // Check that the extraDetails includes context about what changed
            expect(event.type).to.equal("FidesUIChanged");
            expect(event.detail.extraDetails).to.have.property("trigger");
            expect(event.detail.extraDetails.trigger).to.deep.include({
              label: PURPOSE_4.name,
              checked: true,
            });
            expect(event.detail.extraDetails.preference).to.deep.include({
              type: "tcf_purpose_consent",
              key: "tcf_purpose_consent_4",
            });
          });

        // Enable the second purpose toggle
        cy.getByTestId(`toggle-${PURPOSE_6.name}`).click();
        cy.get("@FidesUIChanged").its("callCount").should("equal", 2);
        cy.get("@FidesUIChanged")
          .its("secondCall.args.0")
          .then((event: CustomEvent) => {
            // Check that the extraDetails includes context about what changed
            expect(event.type).to.equal("FidesUIChanged");
            expect(event.detail.extraDetails).to.have.property("trigger");
            expect(event.detail.extraDetails.trigger).to.deep.include({
              label: PURPOSE_6.name,
              checked: true,
            });
            expect(event.detail.extraDetails.preference).to.deep.include({
              type: "tcf_purpose_consent",
              key: "tcf_purpose_consent_6",
            });
          });

        // Switch the first purpose toggle back off
        cy.getByTestId(`toggle-${PURPOSE_4.name}`).click();
        cy.get("@FidesUIChanged").its("callCount").should("equal", 3);
        cy.get("@FidesUIChanged")
          .its("thirdCall.args.0")
          .then((event: CustomEvent) => {
            // Check that the extraDetails includes context about what changed
            expect(event.type).to.equal("FidesUIChanged");
            expect(event.detail.extraDetails).to.have.property("trigger");
            expect(event.detail.extraDetails.trigger).to.deep.include({
              label: PURPOSE_4.name,
              checked: false,
            });
            expect(event.detail.extraDetails.preference).to.deep.include({
              type: "tcf_purpose_consent",
              key: "tcf_purpose_consent_4",
            });
          });
      });

      it("can handle group toggle empty states", () => {
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience = payload.items[0];
          const updatedExperience = { ...experience, tcf_purpose_consents: [] };
          stubTCFExperience({
            experienceFullOverride: updatedExperience,
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.get("#fides-modal-link").click();
            cy.getByTestId(`records-list-purposes`).should("not.exist");
          });
        });
      });

      it("separates purpose tab by legal bases", () => {
        const legintSpecialPurposeName =
          "Deliver and present advertising and content";
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience = payload.items[0];
          const specialPurposeCopy = JSON.parse(
            JSON.stringify(experience.tcf_special_purposes[0]),
          );
          const legintSpecialPurpose = {
            ...specialPurposeCopy,
            id: 2,
            name: legintSpecialPurposeName,
            legal_bases: ["Legitimate interests"],
          };
          experience.tcf_special_purposes.push(legintSpecialPurpose);
          stubTCFExperience({
            experienceFullOverride: experience,
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.get("#fides-modal-link").click();
            // First check consent page
            const consentPurposes = [
              PURPOSE_4,
              PURPOSE_6,
              PURPOSE_7,
              PURPOSE_9,
            ];
            consentPurposes.forEach((p) => {
              cy.getByTestId(`toggle-${p.name}`);
            });
            cy.get("span").contains(SPECIAL_PURPOSE_1.name);
            cy.get("span")
              .contains(legintSpecialPurposeName)
              .should("not.exist");
            cy.get("span").contains(PURPOSE_4.name).click();
            // scroll to the vendor list
            cy.get(".fides-tcf-purpose-vendor-list").first().scrollIntoView();
            cy.get(".fides-tcf-purpose-vendor-list")
              .contains(VENDOR_1.name)
              .should("be.visible");
            cy.get(".fides-tcf-purpose-vendor-list")
              .contains(VENDOR_2.name)
              .should("not.be.visible");
            cy.getByTestId(`toggle-${PURPOSE_2.name}`).should("not.exist");

            // Now check legint page
            cy.get("button").contains("Legitimate interest").click();
            consentPurposes.forEach((p) => {
              cy.getByTestId(`toggle-${p.name}`).should("not.exist");
            });
            cy.getByTestId(`toggle-${PURPOSE_2.name}`);
            cy.get("span").contains(legintSpecialPurposeName);
            cy.get("span").contains(SPECIAL_PURPOSE_1.name).should("not.exist");
            cy.get("span").contains(PURPOSE_2.name).click();
            cy.get(".fides-tcf-purpose-vendor-list").first().scrollIntoView();
            cy.get(".fides-tcf-purpose-vendor-list")
              .contains(VENDOR_1.name)
              .should("not.be.visible");
            cy.get(".fides-tcf-purpose-vendor-list")
              .contains(VENDOR_2.name)
              .should("be.visible");
          });
        });
      });

      it("renders toggles in both legal bases views if both exist", () => {
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience = payload.items[0];
          // Add a vendor legitimate interest which is the same as vendor consent
          // eslint-disable-next-line @typescript-eslint/naming-convention
          const tcf_vendor_legitimate_interests = [
            {
              ...experience.tcf_vendor_consents[0],
              default_preference: "opt_out",
              purpose_legitimate_interests: [PURPOSE_2.id],
            },
          ];
          const updatedExperience = {
            ...experience,
            tcf_vendor_legitimate_interests,
          };
          stubTCFExperience({
            experienceFullOverride: updatedExperience,
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.get("#fides-modal-link").click();
            cy.get("#fides-tab-vendors").click();
            cy.get("#fides-panel-vendors").within(() => {
              // Toggle the consent toggle on
              cy.getByTestId(`toggle-${VENDOR_1.name}`).click();
              cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
                cy.get("input").should("be.checked");
              });
              cy.get("button").contains("Legitimate interest").click();
              cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
                cy.get("input").should("not.be.checked");
              });
            });
            cy.get("@FidesUIChanged").should("have.been.calledOnce");
          });
        });
      });
    });

    describe("saving preferences", () => {
      testCustomPurposes.forEach((includeCustomPurposes) => {
        describe(`sets preferences ${includeCustomPurposes ? `with` : `without`} custom purposes`, () => {
          const vendorsDisclosed = ".IABE";
          beforeEach(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
            stubTCFExperience({ includeCustomPurposes });

            cy.get("div#fides-banner").within(() => {
              cy.get("#fides-button-group").within(() => {
                cy.get("button").contains("Manage preferences").click();
              });
            });
          });
          it("can opt in to all", () => {
            cy.getByTestId("consent-modal").within(() => {
              cy.get("button").contains("Opt in to all").click();
              cy.wait("@patchPrivacyPreference").then((interception) => {
                cy.get("@FidesUIChanged").should("not.have.been.called");
                const { body } = interception.request;
                expect(body.method).to.eql(ConsentMethod.ACCEPT);
                expect(body.purpose_consent_preferences).to.eql([
                  {
                    id: PURPOSE_4.id,
                    preference: "opt_in",
                  },
                  {
                    id: PURPOSE_6.id,
                    preference: "opt_in",
                  },
                  {
                    id: PURPOSE_7.id,
                    preference: "opt_in",
                  },
                  {
                    id: PURPOSE_9.id,
                    preference: "opt_in",
                  },
                ]);
                expect(body.purpose_legitimate_interests_preferences).to.eql([
                  {
                    id: PURPOSE_2.id,
                    preference: "opt_in",
                  },
                ]);
                expect(body.special_purpose_preferences).to.eql(undefined);
                expect(body.feature_preferences).to.eql(undefined);
                expect(body.special_feature_preferences).to.eql([
                  {
                    id: SPECIAL_FEATURE_1.id,
                    preference: "opt_in",
                  },
                ]);
                expect(body.vendor_consent_preferences).to.eql([
                  {
                    id: VENDOR_1.id,
                    preference: "opt_in",
                  },
                ]);
                expect(body.vendor_legitimate_interests_preferences).to.eql([]);
                expect(body.system_legitimate_interests_preferences).to.eql([
                  {
                    id: SYSTEM_1.id,
                    preference: "opt_in",
                  },
                ]);
                expect(body.system_consent_preferences).to.eql([]);
              });
            });
            // Verify the cookie on save
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value),
              );
              expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
                ConsentMethod.ACCEPT,
              );
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeConsents",
                ids: [PURPOSE_9.id, PURPOSE_6.id, PURPOSE_7.id, PURPOSE_4.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeLegitimateInterests",
                ids: [PURPOSE_2.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "specialFeatureOptins",
                ids: [SPECIAL_FEATURE_1.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorConsents",
                ids: [fidesVendorIdToId(VENDOR_1.id)],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorLegitimateInterests",
                ids: [fidesVendorIdToId(VENDOR_1.id)],
              });
              expect(
                cookieKeyConsent.tcf_consent.system_consent_preferences,
              ).to.eql({});
              expect(
                cookieKeyConsent.tcf_consent
                  .system_legitimate_interests_preferences,
              )
                .property(`${SYSTEM_1.id}`)
                .is.eql(true);

              if (includeCustomPurposes) {
                // Confirm custom purposes are persisted to the cookie
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_1)
                  .is.eql(true);
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_2)
                  .is.eql(true);
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_3)
                  .is.eql(true);
                expect(cookieKeyConsent.fides_meta)
                  .property("consentMethod")
                  .is.eql(ConsentMethod.ACCEPT);
              }

              // Confirm vendors_disclosed section does not exist
              expect(cookieKeyConsent.fides_string).to.not.contain(
                vendorsDisclosed,
              );
            });
            // verify the data layer variables
            cy.get("@dataLayerPush")
              .should("have.been.callCount", 7) // FidesReady + FidesInitialized + FidesUIShown (banner) + FidesUIShown (modal) + FidesModalClosed + FidesUpdating + FidesUpdated
              // First call should be from initialization ready, before the user accepts all
              .its("firstCall.args.0")
              .then((actual) => Cypress._.omit(actual, "Fides.timestamp"))
              .should("deep.equal", {
                event: "FidesReady",
                Fides: {
                  consent: includeCustomPurposes
                    ? {
                        advertising: false,
                        analytics_opt_out: true,
                        essential: true,
                      }
                    : {},
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
                  consent: includeCustomPurposes
                    ? {
                        advertising: false,
                        analytics_opt_out: true,
                        essential: true,
                      }
                    : {},
                  extraDetails: {
                    consentMethod: undefined,
                    shouldShowExperience: true,
                    trigger: { origin: "fides" },
                  },
                  fides_string: undefined,
                });
              });

            // Verify FidesUIShown events (banner and modal)
            cy.get("@dataLayerPush")
              .its("args")
              .then((args) => {
                // Banner shown event
                const bannerEvent = args[2][0];
                expect(bannerEvent.event).to.equal("FidesUIShown");
                expect(
                  bannerEvent.Fides.extraDetails.servingComponent,
                ).to.equal("tcf_banner");

                // Modal shown event
                const modalEvent = args[3][0];
                expect(modalEvent.event).to.equal("FidesUIShown");
                expect(modalEvent.Fides.extraDetails.servingComponent).to.equal(
                  "tcf_overlay",
                );

                // Modal closed event
                const modalClosedEvent = args[4][0];
                expect(modalClosedEvent.event).to.equal("FidesModalClosed");
                expect(
                  modalClosedEvent.Fides.extraDetails.servingComponent,
                ).to.equal("tcf_overlay");
              });

            // FidesUpdating call
            cy.get("@dataLayerPush")
              .its("args")
              .then((args) => {
                const call = args[5][0];
                expect(call.event).to.equal("FidesUpdating");
                expect(call.Fides).to.deep.include({
                  consent: includeCustomPurposes
                    ? {
                        advertising: true,
                        analytics_opt_out: true,
                        essential: true,
                      }
                    : {},
                  extraDetails: {
                    consentMethod: "accept",
                    servingComponent: "tcf_overlay",
                    trigger: {
                      type: "button",
                      label: "Opt in to all",
                      origin: "fides",
                    },
                  },
                });
                expect(call.Fides.fides_string).to.contain(",2~~dv.");
              });

            // FidesUpdated call
            cy.get("@dataLayerPush")
              .its("args")
              .then((args) => {
                const call = args[6][0];
                expect(call.event).to.equal("FidesUpdated");
                expect(call.Fides).to.deep.include({
                  consent: includeCustomPurposes
                    ? {
                        advertising: true,
                        analytics_opt_out: true,
                        essential: true,
                      }
                    : {},
                  extraDetails: {
                    consentMethod: "accept",
                    servingComponent: "tcf_overlay",
                    trigger: {
                      type: "button",
                      label: "Opt in to all",
                      origin: "fides",
                    },
                  },
                });
                expect(call.Fides.fides_string).to.contain(",2~~dv.");
              });
          });

          it("can opt out of all", () => {
            cy.getByTestId("consent-modal").within(() => {
              cy.get("button").contains("Opt out of all").click();
              cy.wait("@patchPrivacyPreference").then((interception) => {
                cy.get("@FidesUIChanged").should("not.have.been.called");
                const { body } = interception.request;
                expect(interception.request.body.method).to.eql(
                  ConsentMethod.REJECT,
                );
                expect(body.purpose_consent_preferences).to.eql([
                  {
                    id: PURPOSE_4.id,
                    preference: "opt_out",
                  },
                  {
                    id: PURPOSE_6.id,
                    preference: "opt_out",
                  },
                  {
                    id: PURPOSE_7.id,
                    preference: "opt_out",
                  },
                  {
                    id: PURPOSE_9.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.purpose_legitimate_interests_preferences).to.eql([
                  {
                    id: PURPOSE_2.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.special_purpose_preferences).to.eql(undefined);
                expect(body.feature_preferences).to.eql(undefined);
                expect(body.special_feature_preferences).to.eql([
                  {
                    id: SPECIAL_FEATURE_1.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.vendor_consent_preferences).to.eql([
                  {
                    id: VENDOR_1.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.vendor_legitimate_interests_preferences).to.eql([]);
                expect(body.system_legitimate_interests_preferences).to.eql([
                  {
                    id: SYSTEM_1.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.system_consent_preferences).to.eql([]);
              });
            });
            // Verify the cookie on save
            cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
              cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
                const cookieKeyConsent: FidesCookie = JSON.parse(
                  decodeURIComponent(cookie!.value),
                );
                expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
                  ConsentMethod.REJECT,
                );
                assertTcOptIns({
                  cookie: cookieKeyConsent,
                  modelType: "purposeConsents",
                  ids: [],
                });
                assertTcOptIns({
                  cookie: cookieKeyConsent,
                  modelType: "purposeLegitimateInterests",
                  ids: [],
                });
                assertTcOptIns({
                  cookie: cookieKeyConsent,
                  modelType: "specialFeatureOptins",
                  ids: [],
                });
                assertTcOptIns({
                  cookie: cookieKeyConsent,
                  modelType: "vendorConsents",
                  ids: [],
                });
                assertTcOptIns({
                  cookie: cookieKeyConsent,
                  modelType: "vendorLegitimateInterests",
                  ids: [fidesVendorIdToId(VENDOR_1.id)],
                });
                expect(
                  cookieKeyConsent.tcf_consent.system_consent_preferences,
                ).to.eql({});
                expect(
                  cookieKeyConsent.tcf_consent
                    .system_legitimate_interests_preferences,
                )
                  .property(`${SYSTEM_1.id}`)
                  .is.eql(false);

                if (includeCustomPurposes) {
                  // Confirm custom purposes are persisted to the cookie
                  expect(cookieKeyConsent.consent)
                    .property(PRIVACY_NOTICE_KEY_1)
                    .is.eql(false);
                  expect(cookieKeyConsent.consent)
                    .property(PRIVACY_NOTICE_KEY_2)
                    .is.eql(true);
                  expect(cookieKeyConsent.consent)
                    .property(PRIVACY_NOTICE_KEY_3)
                    .is.eql(false);
                  expect(cookieKeyConsent.fides_meta)
                    .property("consentMethod")
                    .is.eql(ConsentMethod.REJECT);
                }

                // Confirm vendors_disclosed section does not exist
                expect(cookieKeyConsent.fides_string).to.not.contain(
                  vendorsDisclosed,
                );
              });
            });
          });

          it("can opt in to some and opt out of others", () => {
            cy.getByTestId("consent-modal").within(() => {
              if (includeCustomPurposes) {
                // Custom notice should start off toggled off
                cy.getByTestId("toggle-Advertising English").within(() => {
                  cy.get("input").should("not.be.checked");
                });
                // Opt-out notice should start toggled on
                cy.getByTestId("toggle-Analytics").within(() => {
                  cy.get("input").should("be.checked");
                });
                // Notice-only should start off toggled on
                cy.getByTestId("toggle-Essential").within(() => {
                  cy.get("input").should("be.checked");
                });
                // opt in to opt-in custom notice
                cy.getByTestId(`toggle-Advertising English`).click();
              }
              // opt in to purpose 4
              cy.getByTestId(`toggle-${PURPOSE_4.name}`).click();
              cy.get("#fides-tab-features").click();
              // opt in to special feat 1
              cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).click();

              cy.get("#fides-tab-vendors").click();
              cy.get("#fides-panel-vendors").within(() => {
                cy.get("button").contains("Legitimate interest").click();
              });
              // opt out of system 1 (default is opt-in)
              cy.getByTestId(`toggle-${SYSTEM_1.name}`).click();
              cy.get("button").contains("Save").click();
              cy.get("@FidesUIChanged")
                .its("callCount")
                .should("equal", includeCustomPurposes ? 4 : 3);
              cy.wait("@patchPrivacyPreference").then((interception) => {
                const { body } = interception.request;
                expect(interception.request.body.method).to.eql(
                  ConsentMethod.SAVE,
                );
                if (includeCustomPurposes) {
                  expect(body.preferences).to.eql([
                    {
                      preference: "opt_in",
                      privacy_notice_history_id:
                        "pri_notice-history-advertising-en-000",
                    },
                    {
                      preference: "opt_in",
                      privacy_notice_history_id:
                        "pri_notice-history-analytics-en-000",
                    },
                    {
                      preference: "acknowledge",
                      privacy_notice_history_id:
                        "pri_notice-history-essential-en-000",
                    },
                  ]);
                }
                expect(body.purpose_consent_preferences).to.eql([
                  {
                    id: PURPOSE_4.id,
                    preference: "opt_in",
                  },
                  {
                    id: PURPOSE_6.id,
                    preference: "opt_out",
                  },
                  {
                    id: PURPOSE_7.id,
                    preference: "opt_out",
                  },
                  {
                    id: PURPOSE_9.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.purpose_legitimate_interests_preferences).to.eql([
                  {
                    id: PURPOSE_2.id,
                    preference: "opt_in",
                  },
                ]);
                expect(body.special_purpose_preferences).to.eql(undefined);
                expect(body.feature_preferences).to.eql(undefined);
                expect(body.special_feature_preferences).to.eql([
                  {
                    id: SPECIAL_FEATURE_1.id,
                    preference: "opt_in",
                  },
                ]);
                expect(body.vendor_consent_preferences).to.eql([
                  {
                    id: VENDOR_1.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.vendor_legitimate_interests_preferences).to.eql([]);
                expect(body.system_legitimate_interests_preferences).to.eql([
                  {
                    id: SYSTEM_1.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.system_consent_preferences).to.eql([]);
              });
            });
            // Verify the cookie on save
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value),
              );
              expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
                ConsentMethod.SAVE,
              );
              if (includeCustomPurposes) {
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_1)
                  .is.eql(true);
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_2)
                  .is.eql(true);
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_3)
                  .is.eql(true);
              }
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeConsents",
                ids: [PURPOSE_4.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeLegitimateInterests",
                ids: [PURPOSE_2.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "specialFeatureOptins",
                ids: [SPECIAL_FEATURE_1.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorConsents",
                ids: [],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorLegitimateInterests",
                ids: [fidesVendorIdToId(VENDOR_1.id)],
              });
              expect(
                cookieKeyConsent.tcf_consent
                  .system_legitimate_interests_preferences,
              )
                .property(`${SYSTEM_1.id}`)
                .is.eql(false);
              expect(
                cookieKeyConsent.tcf_consent.system_consent_preferences,
              ).to.eql({});
              // Confirm vendors_disclosed section does not exist
              expect(cookieKeyConsent.fides_string).to.not.contain(
                vendorsDisclosed,
              );
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeConsents",
                ids: [PURPOSE_4.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeLegitimateInterests",
                ids: [PURPOSE_2.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "specialFeatureOptins",
                ids: [SPECIAL_FEATURE_1.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorConsents",
                ids: [],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorLegitimateInterests",
                ids: [fidesVendorIdToId(VENDOR_1.id)],
              });
              expect(
                cookieKeyConsent.tcf_consent
                  .system_legitimate_interests_preferences,
              )
                .property(`${SYSTEM_1.id}`)
                .is.eql(false);
              expect(
                cookieKeyConsent.tcf_consent.system_consent_preferences,
              ).to.eql({});
              // Confirm vendors_disclosed section does not exist
              expect(cookieKeyConsent.fides_string).to.not.contain(
                vendorsDisclosed,
              );
            });
          });

          it("remembers consent when re-opening the modal", () => {
            cy.getByTestId("consent-modal").within(() => {
              // opt in to purpose 4
              cy.getByTestId(`toggle-${PURPOSE_4.name}`).click();
              if (includeCustomPurposes) {
                cy.getByTestId(`toggle-Advertising English`).click();
              }
              cy.get("button").contains("Save").click();
            });
            cy.wait("@patchPrivacyPreference");
            cy.get("#fides-modal-link").click();
            cy.getByTestId(`toggle-${PURPOSE_4.name}`).within(() => {
              cy.get("input").should("be.checked");
            });
            if (includeCustomPurposes) {
              cy.getByTestId(`toggle-Advertising English`).within(() => {
                cy.get("input").should("be.checked");
              });
            }
          });

          it("can opt out of some custom consent and some tcf consent", () => {
            cy.getByTestId("consent-modal").within(() => {
              if (includeCustomPurposes) {
                // Custom notice should start off toggled off
                cy.getByTestId("toggle-Advertising English").within(() => {
                  cy.get("input").should("not.be.checked");
                });
                // Opt-out notice should start toggled on
                cy.getByTestId("toggle-Analytics").within(() => {
                  cy.get("input").should("be.checked");
                });
                cy.getByTestId("toggle-Advertising English").click();
                // Notice-only should start off toggled on
                cy.getByTestId("toggle-Essential").within(() => {
                  cy.get("input").should("be.checked");
                });
                // opt out to opt-out custom notice
                cy.getByTestId(`toggle-Analytics`).click();
              }
              // opt in to purpose 4
              cy.getByTestId(`toggle-${PURPOSE_4.name}`).click();
              cy.get("#fides-tab-features").click();
              // opt in to special feat 1
              cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).click();

              cy.get("#fides-tab-vendors").click();
              cy.get("#fides-panel-vendors").within(() => {
                cy.get("button").contains("Legitimate interest").click();
              });
              // opt out of system 1 (default is opt-in)
              cy.getByTestId(`toggle-${SYSTEM_1.name}`).click();
              cy.get("button").contains("Save").click();
              cy.get("@FidesUIChanged")
                .its("callCount")
                .should("equal", includeCustomPurposes ? 5 : 3);
              cy.wait("@patchPrivacyPreference").then((interception) => {
                const { body } = interception.request;
                expect(interception.request.body.method).to.eql(
                  ConsentMethod.SAVE,
                );
                if (includeCustomPurposes) {
                  expect(body.preferences).to.eql([
                    {
                      preference: "opt_in",
                      privacy_notice_history_id:
                        "pri_notice-history-advertising-en-000",
                    },
                    {
                      preference: "opt_out",
                      privacy_notice_history_id:
                        "pri_notice-history-analytics-en-000",
                    },
                    {
                      preference: "acknowledge",
                      privacy_notice_history_id:
                        "pri_notice-history-essential-en-000",
                    },
                  ]);
                }
                expect(body.purpose_consent_preferences).to.eql([
                  {
                    id: PURPOSE_4.id,
                    preference: "opt_in",
                  },
                  {
                    id: PURPOSE_6.id,
                    preference: "opt_out",
                  },
                  {
                    id: PURPOSE_7.id,
                    preference: "opt_out",
                  },
                  {
                    id: PURPOSE_9.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.purpose_legitimate_interests_preferences).to.eql([
                  {
                    id: PURPOSE_2.id,
                    preference: "opt_in",
                  },
                ]);
                expect(body.special_purpose_preferences).to.eql(undefined);
                expect(body.feature_preferences).to.eql(undefined);
                expect(body.special_feature_preferences).to.eql([
                  {
                    id: SPECIAL_FEATURE_1.id,
                    preference: "opt_in",
                  },
                ]);
                expect(body.vendor_consent_preferences).to.eql([
                  {
                    id: VENDOR_1.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.vendor_legitimate_interests_preferences).to.eql([]);
                expect(body.system_legitimate_interests_preferences).to.eql([
                  {
                    id: SYSTEM_1.id,
                    preference: "opt_out",
                  },
                ]);
                expect(body.system_consent_preferences).to.eql([]);
              });
            });
            // Verify the cookie on save
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value),
              );
              expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
                ConsentMethod.SAVE,
              );
              if (includeCustomPurposes) {
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_1)
                  .is.eql(true);
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_2)
                  .is.eql(true);
                expect(cookieKeyConsent.consent)
                  .property(PRIVACY_NOTICE_KEY_3)
                  .is.eql(false);
              }
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeConsents",
                ids: [PURPOSE_4.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "purposeLegitimateInterests",
                ids: [PURPOSE_2.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "specialFeatureOptins",
                ids: [SPECIAL_FEATURE_1.id],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorConsents",
                ids: [],
              });
              assertTcOptIns({
                cookie: cookieKeyConsent,
                modelType: "vendorLegitimateInterests",
                ids: [fidesVendorIdToId(VENDOR_1.id)],
              });
              expect(
                cookieKeyConsent.tcf_consent
                  .system_legitimate_interests_preferences,
              )
                .property(`${SYSTEM_1.id}`)
                .is.eql(false);
              expect(
                cookieKeyConsent.tcf_consent.system_consent_preferences,
              ).to.eql({});
              // Confirm vendors_disclosed section does not exist
              expect(cookieKeyConsent.fides_string).to.not.contain(
                vendorsDisclosed,
              );
            });
          });
        });
      });

      it("calls custom save preferences API fn instead of internal Fides API when it is provided in Fides.init", () => {
        const apiOptions = {
          /* eslint-disable @typescript-eslint/no-unused-vars */
          savePreferencesFn: async (
            consentMethod: ConsentMethod,
            consent: NoticeConsent,
            fides_string: string | undefined,
            experience: PrivacyExperience,
          ): Promise<void> => {},
          /* eslint-enable @typescript-eslint/no-unused-vars */
        };
        const spyObject = cy
          .spy(apiOptions, "savePreferencesFn")
          .as("mockSavePreferencesFn");

        stubTCFExperience({
          stubOptions: { apiOptions },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").within(() => {
            cy.get("#fides-button-group").within(() => {
              cy.get("button").contains("Manage preferences").click();
            });
          });
          cy.getByTestId("consent-modal").within(() => {
            cy.get("button").contains("Opt out of all").click();
            cy.get("@FidesUpdated")
              .should("have.been.calledOnce")
              .its("lastCall.args.0.detail.extraDetails.consentMethod")
              .then((consentMethod) => {
                expect(consentMethod).to.eql(ConsentMethod.REJECT);
                // eslint-disable-next-line @typescript-eslint/no-unused-expressions
                expect(spyObject).to.be.called;
                const spy = spyObject.getCalls();
                const { args } = spy[0];
                expect(args[0]).to.equal(ConsentMethod.REJECT);
                expect(args[1]).to.be.a("object");
                // the TC str is dynamically updated upon save preferences with diff timestamp, so we do a fuzzy match
                expect(args[2]).to.contain("AA,2~~dv.");
                expect(args[3]).to.be.a("object");
                // timeout means API call not made, which is expected
                cy.on("fail", (error) => {
                  if (error.message.indexOf("Timed out retrying") !== 0) {
                    throw error;
                  }
                });
                // check that preferences aren't sent to Fides API
                cy.wait("@patchPrivacyPreference", {
                  requestTimeout: 100,
                }).then((xhr) => {
                  assert.isNull(xhr?.response?.body);
                });
              });
          });
        });
      });

      it("skips saving preferences to API when disable save is set", () => {
        stubTCFExperience({
          stubOptions: { fidesDisableSaveApi: true },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("#fides-modal-link").click();
          cy.getByTestId("consent-modal").within(() => {
            cy.get("button").contains("Opt out of all").click();
            // timeout means API call not made, which is expected
            cy.on("fail", (error) => {
              if (error.message.indexOf("Timed out retrying") !== 0) {
                throw error;
              }
            });
            // check that preferences aren't sent to Fides API
            cy.wait("@patchPrivacyPreference", {
              requestTimeout: 100,
            }).then((xhr) => {
              assert.isNull(xhr?.response?.body);
            });
          });
          // The cookie should still get updated
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
              ConsentMethod.REJECT,
            );
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "purposeConsents",
              ids: [],
            });
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "purposeLegitimateInterests",
              ids: [],
            });
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "specialFeatureOptins",
              ids: [],
            });
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "vendorConsents",
              ids: [],
            });
            assertTcOptIns({
              cookie: cookieKeyConsent,
              modelType: "vendorLegitimateInterests",
              ids: [fidesVendorIdToId(VENDOR_1.id)],
            });
            expect(
              cookieKeyConsent.tcf_consent.system_consent_preferences,
            ).to.eql({});
            expect(
              cookieKeyConsent.tcf_consent
                .system_legitimate_interests_preferences,
            )
              .property(`${SYSTEM_1.id}`)
              .is.eql(false);
          });
        });
      });

      it("skips saving preferences to API when disable save is set via cookie", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        cy.getCookie("fides_disable_save_api").should("not.exist");
        cy.setCookie("fides_disable_save_api", "true");
        stubTCFExperience({});
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("#fides-modal-link").click();
          cy.getByTestId("consent-modal").within(() => {
            cy.get("button").contains("Opt out of all").click();
            // timeout means API call not made, which is expected
            cy.on("fail", (error) => {
              if (error.message.indexOf("Timed out retrying") !== 0) {
                throw error;
              }
            });
            // check that preferences aren't sent to Fides API
            cy.wait("@patchPrivacyPreference", {
              requestTimeout: 100,
            }).then((xhr) => {
              assert.isNull(xhr?.response?.body);
            });
          });
        });
      });

      it("skips saving preferences to API when disable save is set via query param", () => {
        cy.getCookie("fides_string").should("not.exist");
        stubTCFExperience({
          demoPageQueryParams: { fides_disable_save_api: "true" },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("#fides-modal-link").click();
          cy.getByTestId("consent-modal").within(() => {
            cy.get("button").contains("Opt out of all").click();
            // timeout means API call not made, which is expected
            cy.on("fail", (error) => {
              if (error.message.indexOf("Timed out retrying") !== 0) {
                throw error;
              }
            });
            // check that preferences aren't sent to Fides API
            cy.wait("@patchPrivacyPreference", {
              requestTimeout: 100,
            }).then((xhr) => {
              assert.isNull(xhr?.response?.body);
            });
          });
        });
      });

      it("skips saving preferences to API when disable save is set via window obj", () => {
        cy.getCookie("fides_string").should("not.exist");
        stubTCFExperience({
          demoPageWindowParams: { fides_disable_save_api: "true" },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("#fides-modal-link").click();
          cy.getByTestId("consent-modal").within(() => {
            cy.get("button").contains("Opt out of all").click();
            // timeout means API call not made, which is expected
            cy.on("fail", (error) => {
              if (error.message.indexOf("Timed out retrying") !== 0) {
                throw error;
              }
            });
            // check that preferences aren't sent to Fides API
            cy.wait("@patchPrivacyPreference", {
              requestTimeout: 100,
            }).then((xhr) => {
              assert.isNull(xhr?.response?.body);
            });
          });
        });
      });
    });

    describe("Vendor overrides", () => {
      it("adds Legitimate Interest vendors to Preferences list when overriden", () => {
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience = payload.items[0];
          // mimics behavior of a vendor override, where DoubleVerify is added to the
          // preferences list instead of Legitimate Interest vendor
          experience.tcf_vendor_consents = [
            {
              id: "gvl.3",
              name: "DoubleVerify",
              default_preference: "opt_out",
              purpose_consents: [
                {
                  ...PURPOSE_2,
                  retention_period: "45",
                },
              ],
            },
          ];
          experience.tcf_vendor_legitimate_interests = [];
          experience.tcf_vendor_relationships = [
            {
              id: "gvl.3",
              has_vendor_id: true,
              name: "DoubleVerify",
              special_purposes: [
                {
                  id: 1,
                  name: "Ensure security, prevent and detect fraud, and fix errors",
                  retention_period: "45",
                },
                {
                  id: 2,
                  name: "Deliver and present advertising and content",
                  retention_period: "45",
                },
              ],
            },
          ];
          stubTCFExperience({
            experienceFullOverride: experience,
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.get("#fides-modal-link").click();
            cy.get("#fides-tab-vendors").click();
            cy.get("#fides-panel-vendors").within(() => {
              // should exist in the Consent list and not be checked yet
              cy.getByTestId("toggle-DoubleVerify")
                .find("input")
                .should("exist");
              cy.getByTestId("toggle-DoubleVerify")
                .find("input")
                .should("not.be.checked");
            });
            cy.getByTestId("fides-modal-content").within(() => {
              cy.getByTestId("Opt in to all-btn").click();
            });
            // Verify the TCF String has the vendor override
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value),
              );
              expect(cookieKeyConsent.fides_string).to.contain(
                "GXABBENArEoABaAAEAAAAAAABiAAAAMJABAAGOgAgADKQAQABgA", // excludes date information for testing
              );
            });
          });
        });
      });
    });
  });

  describe("when fides_embed is true", () => {
    describe("when fides_disable_banner is false", () => {
      it("renders the embedded layer 1 banner", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubTCFExperience({ stubOptions: { fidesEmbed: true } });
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        cy.get("div#fides-banner").should("be.visible");
        cy.get("div#fides-banner #fides-banner-title").contains(
          "[banner] Manage your consent",
        );
      });
      it(
        "waits until the embed tag is available",
        { defaultCommandTimeout: 200 },
        () => {
          const delay = 1000;
          cy.on("window:before:load", (win: { render_delay: number }) => {
            // eslint-disable-next-line no-param-reassign
            win.render_delay = delay;
            cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
            stubTCFExperience({ stubOptions: { fidesEmbed: true } });
            cy.get("@FidesUIShown").should("not.have.been.called");
            cy.get("div#fides-banner").should("not.exist");
            // eslint-disable-next-line cypress/no-unnecessary-waiting
            cy.wait(delay); // wait until delay is over
            cy.get("@FidesUIShown").should("have.been.calledOnce");
            cy.get("div#fides-banner").should("be.visible");
          });
        },
      );
    });

    describe("when fides_disable_banner is true (Layer 2 only)", () => {
      it("renders the embedded second layer and can render tabs", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubTCFExperience({
          stubOptions: { fidesEmbed: true, fidesDisableBanner: true },
        });
        cy.get("#fides-tab-purposes");
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        checkDefaultExperienceRender();
      });
      it("can opt in to some and opt out of others", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubTCFExperience({
          stubOptions: { fidesEmbed: true, fidesDisableBanner: true },
        });
        cy.getByTestId("consent-content").within(() => {
          cy.getByTestId(`toggle-${PURPOSE_4.name}`).click();
          cy.get("#fides-tab-features").click();
          cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).click();

          cy.get("#fides-tab-vendors").click();
          cy.get("#fides-panel-vendors").within(() => {
            cy.get("button").contains("Legitimate interest").click();
          });
          cy.getByTestId(`toggle-${SYSTEM_1.name}`).click();
        });
        cy.get("button").contains("Save").click();
        cy.wait("@patchPrivacyPreference").then((interception) => {
          const { body } = interception.request;
          expect(interception.request.body.method).to.eql(ConsentMethod.SAVE);
          expect(body.purpose_consent_preferences).to.eql([
            { id: PURPOSE_4.id, preference: "opt_in" },
            { id: PURPOSE_6.id, preference: "opt_out" },
            { id: PURPOSE_7.id, preference: "opt_out" },
            { id: PURPOSE_9.id, preference: "opt_out" },
          ]);
          expect(body.purpose_legitimate_interests_preferences).to.eql([
            { id: PURPOSE_2.id, preference: "opt_in" },
          ]);
          expect(body.special_purpose_preferences).to.eql(undefined);
          expect(body.feature_preferences).to.eql(undefined);
          expect(body.special_feature_preferences).to.eql([
            { id: SPECIAL_FEATURE_1.id, preference: "opt_in" },
          ]);
          expect(body.vendor_consent_preferences).to.eql([
            { id: VENDOR_1.id, preference: "opt_out" },
          ]);
          expect(body.vendor_legitimate_interests_preferences).to.eql([]);
          expect(body.system_legitimate_interests_preferences).to.eql([
            { id: SYSTEM_1.id, preference: "opt_out" },
          ]);
          expect(body.system_consent_preferences).to.eql([]);
        });
        // embed modal should not close on preferences save
        cy.getByTestId("consent-content").should("exist");
        // Verify the cookie on save
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value),
          );
          expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
            ConsentMethod.SAVE,
          );
          assertTcOptIns({
            cookie: cookieKeyConsent,
            modelType: "purposeConsents",
            ids: [PURPOSE_4.id],
          });
          assertTcOptIns({
            cookie: cookieKeyConsent,
            modelType: "purposeLegitimateInterests",
            ids: [PURPOSE_2.id],
          });
          assertTcOptIns({
            cookie: cookieKeyConsent,
            modelType: "specialFeatureOptins",
            ids: [SPECIAL_FEATURE_1.id],
          });
          assertTcOptIns({
            cookie: cookieKeyConsent,
            modelType: "vendorConsents",
            ids: [],
          });
          assertTcOptIns({
            cookie: cookieKeyConsent,
            modelType: "vendorLegitimateInterests",
            ids: [fidesVendorIdToId(VENDOR_1.id)],
          });
          expect(
            cookieKeyConsent.tcf_consent
              .system_legitimate_interests_preferences,
          )
            .property(`${SYSTEM_1.id}`)
            .is.eql(false);
          expect(
            cookieKeyConsent.tcf_consent.system_consent_preferences,
          ).to.eql({});
        });
      });
      it("renders the embedded second layer when fidesEmbed is set via cookie", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        cy.getCookie("fides_embed").should("not.exist");
        cy.setCookie("fides_embed", "true");
        stubTCFExperience({
          stubOptions: { fidesEmbed: true, fidesDisableBanner: true },
        });
        checkDefaultExperienceRender();
      });
      it("renders the embedded second layer when fidesEmbed is set via query param", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubTCFExperience({
          stubOptions: { fidesDisableBanner: true },
          demoPageQueryParams: { fides_embed: "true" },
        });
        checkDefaultExperienceRender();
      });
      it("renders the embedded second layer when fidesEmbed is set via window obj", () => {
        cy.getCookie("fides_string").should("not.exist");
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubTCFExperience({
          stubOptions: { fidesDisableBanner: true },
          demoPageWindowParams: { fides_embed: "true" },
        });
        cy.getByTestId("fides-modal-description").within(() => {
          cy.get(".fides-vendor-count").first().should("have.text", "16");
        });
        checkDefaultExperienceRender();
      });
    });
  });

  describe("CMP API", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubTCFExperience({});
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });
    });

    it("makes API available as soon as possible", () => {
      stubTCFExperience({});
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, (tcData, success) => {
          expect(success).to.eql(true);
          expect(tcData.gdprApplies).to.eql(true);
          expect(tcData.eventStatus).to.eql("tcloaded");
        });
      });
    });

    it("gdpr applies can be overridden to false", () => {
      stubTCFExperience({ stubOptions: { fidesTcfGdprApplies: false } });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, (tcData, success) => {
          expect(success).to.eql(true);
          expect(tcData.gdprApplies).to.eql(false);
        });
      });
    });

    describe("setting fields", () => {
      it("can opt in to all and set legitimate interests", () => {
        cy.get("@FidesUpdated").should("not.have.been.called");
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        cy.get("@FidesUpdated")
          .should("have.been.calledOnce")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.ACCEPT);
          });
        cy.get("@TCFEvent")
          .its("lastCall.args")
          .then(([tcData, success]) => {
            expect(success).to.eql(true);
            expect(tcData.eventStatus).to.eql("useractioncomplete");
            expect(tcData.purpose.consents).to.eql({
              [PURPOSE_4.id]: true,
              [PURPOSE_9.id]: true,
              [PURPOSE_6.id]: true,
              [PURPOSE_7.id]: true,
              1: false,
              2: false,
              3: false,
              5: false,
              8: false,
            });
            expect(tcData.purpose.legitimateInterests).to.eql({
              [PURPOSE_2.id]: true,
              1: false,
            });
            const vendorIdOnly = VENDOR_1.id.split(".")[1];
            expect(tcData.vendor.consents).to.eql({
              1: false,
              [vendorIdOnly]: true,
            });
            expect(tcData.vendor.legitimateInterests).to.eql({
              1: false,
              [vendorIdOnly]: true,
            });
          });
      });

      it("can handle inappropriate legint purposes", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience: PrivacyExperience = payload.items[0];
          // Set purpose with id 4 to LegInt which is not allowed!
          const purpose4 = experience.tcf_purpose_consents?.find(
            (p) => p.id === 4,
          )!;
          experience.tcf_purpose_legitimate_interests?.push(purpose4);
          // Set the corresponding embedded vendor purpose too
          const vendor = experience.tcf_purpose_consents![0];
          experience.tcf_vendor_legitimate_interests?.push({
            ...vendor,
            id: "test",
            purpose_legitimate_interests: [{ id: 4, name: purpose4.name }],
          });
          experience.tcf_vendor_relationships?.push({ ...vendor, id: "test" });
          stubTCFExperience({ experienceFullOverride: experience });
        });
        // Since we've changed windows, redeclare the stub too
        cy.window().then((win) => {
          win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent2"));
        });
        cy.get("div#fides-banner").within(() => {
          cy.get("#fides-button-group").within(() => {
            cy.get("button").contains("Manage preferences").click();
          });
        });
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        cy.get("@FidesUpdated")
          .should("have.been.calledOnce")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.ACCEPT);
          });
        cy.get("@TCFEvent2")
          .its("lastCall.args")
          .then(([tcData, success]) => {
            expect(success).to.eql(true);
            expect(tcData.eventStatus).to.eql("useractioncomplete");
            expect(tcData.purpose.consents).to.eql({
              4: true,
              [PURPOSE_9.id]: true,
              [PURPOSE_6.id]: true,
              [PURPOSE_7.id]: true,
              1: false,
              2: false,
              3: false,
              5: false,
              8: false,
            });
            expect(tcData.purpose.legitimateInterests).to.eql({
              // No id 4 here!
              [PURPOSE_2.id]: true,
              1: false,
            });
            const vendorIdOnly = VENDOR_1.id.split(".")[1];
            expect(tcData.vendor.consents).to.eql({
              1: false,
              [vendorIdOnly]: true,
            });
            expect(tcData.vendor.legitimateInterests).to.eql({
              1: false,
              [vendorIdOnly]: true,
            });
          });
      });
    });
  });

  describe("publisher country code", () => {
    beforeEach(() => {
      cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
        fixture: "consent/notices_served_tcf.json",
      }).as("patchNoticesServed");
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    });

    it("should set default publisher country code (AA) when none is provided", () => {
      stubTCFExperience({});
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("div#fides-banner").should("be.visible");
        cy.get("div#fides-banner").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        cy.get("@TCFEvent")
          .its("lastCall.args")
          .then(([tcData, success]) => {
            expect(success).to.eql(true);
            expect(tcData.publisherCC).to.eql("AA");
            const tcString = tcData.tcString;
            const decodedTCString = TCString.decode(tcString);
            expect(decodedTCString.publisherCountryCode).to.equal("AA");
          });
      });
    });

    it("should set provided publisher country code in TC string", () => {
      cy.fixture("consent/experience_tcf.json").then((payload) => {
        const experience = payload.items[0];
        experience.tcf_publisher_country_code = "US";
        stubTCFExperience({ experienceFullOverride: experience });
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("div#fides-banner").should("be.visible");
        cy.get("div#fides-banner").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        cy.get("@TCFEvent")
          .its("lastCall.args")
          .then(([tcData, success]) => {
            expect(success).to.eql(true);
            expect(tcData.publisherCC).to.eql("US");
            const tcString = tcData.tcString;
            const decodedTCString = TCString.decode(tcString);
            expect(decodedTCString.publisherCountryCode).to.equal("US");
          });
      });
    });
  });
  /**
   * There are the following potential sources of user preferences:
   * 1) fides_string override option (via config.options.fidesString)
   * 2) preferences API (via a custom function)
   * 3) local cookie (via fides_consent cookie)
   * 4) "prefetched" experience (via config.options.experience)
   * 5) experience API (via GET /privacy-experience)
   *
   * These specs test various combinations of those sources of truth and ensure
   * that Fides loads the correct preferences in each case.
   */
  describe("user preferences overrides", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    });

    /**
     * Configure a valid fides_consent cookie with previously saved preferences
     */
    const setFidesCookie = () => {
      const cookie = mockCookie({
        tcf_consent: {
          system_legitimate_interests_preferences: { [SYSTEM_1.id]: false },
        },
        // Purpose 9, Special feature 1, Vendor consent 2
        fides_string: "CPziCYAPziCYAGXABBENATEIAACAAAAAAAAAABEAAAAA",
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
    };

    /**
     * TEST CASE #1:
     * ❌ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ✅ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from local cookie's saved string
     */
    it("prefers preferences from a cookie's fides_string when both cookie and experience exist", () => {
      setFidesCookie();
      stubTCFExperience({ stubOptions: { fidesString: undefined } });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_4.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // also verify that a purpose that was not part of the cookie is also opted out
      // (since it should have no current_preference, and default behavior is opt out)
      cy.getByTestId(`toggle-${PURPOSE_6.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.get("#fides-panel-vendors").within(() => {
        cy.get("button").contains("Legitimate interest").click();
        cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: false,
            2: false,
            1: false,
            3: false,
            5: false,
            8: false,
            9: true,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          const vendorIdOnly = VENDOR_1.id.split(".")[1];
          expect(tcData.vendor.consents).to.eql({
            1: false,
            [vendorIdOnly]: true,
          });
          expect(tcData.vendor.legitimateInterests).to.eql({});
          expect(tcData.specialFeatureOptins).to.eql({
            [SPECIAL_FEATURE_1.id]: true,
          });
        });
    });

    /**
     * TEST CASE #2:
     * ❌ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: ignore all preferences, do not load TCF experience
     */
    it("does nothing when cookie exists but no experience is provided (neither prefetch nor API)", () => {
      setFidesCookie();
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesString: undefined,
          },
          experience: OVERRIDE.UNDEFINED,
        },
        OVERRIDE.UNDEFINED,
        OVERRIDE.EMPTY,
      );
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    /**
     * TEST CASE #3:
     * ❌ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) preferences API (via a custom function)
     * ❌ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: ignore all preferences, do not load TCF experience
     */
    it("does nothing when nothing is provided (neither cookie, nor experience, nor fides_string option)", () => {
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesString: undefined,
          },
          experience: OVERRIDE.UNDEFINED,
        },
        OVERRIDE.UNDEFINED,
        OVERRIDE.EMPTY,
      );
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    /**
     * TEST CASE #4:
     * ✅ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ✅ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from fides_string option
     */
    it("prefers preferences from fides_string option when fides_string, experience, and cookie exist", () => {
      setFidesCookie();
      // Purpose 7, Special Feature 1
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      stubTCFExperience({ stubOptions: { fidesString: fidesStringOverride } });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_4.name}`).within(() => {
        // this purpose was previously set to true from the experience, but it is overridden by the fides_string
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_6.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_7.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      cy.get("button").contains("Legitimate interest").click();
      cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      // this purpose is set to true in the experience, but since it was not defined in the fides_string,
      // it should use false as the default
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.get("#fides-panel-vendors").within(() => {
        cy.get("button").contains("Legitimate interest").click();
        cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql(expectedTCString);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_2.id]: false,
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: true,
            1: false,
            2: false,
            3: false,
            5: false,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });

    /**
     * TEST CASE #5:
     * ✅ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) preferences API (via a custom function)
     * ❌ 3) local cookie (via fides_consent cookie)
     * ✅ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from fides_string option
     */
    it("prefers preferences from fides_string option when both fides_string and experience is provided and cookie does not exist", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      stubTCFExperience({ stubOptions: { fidesString: fidesStringOverride } });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_4.name}`).within(() => {
        // this purpose was previously set to true from the experience, but it is overridden by the fides_string
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_6.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_7.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      cy.get("button").contains("Legitimate interest").click();
      cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      // this purpose is set to true in the experience, but since it was not defined in the fides_string,
      // it should use false as the default
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.get("#fides-panel-vendors").within(() => {
        cy.get("button").contains("Legitimate interest").click();
        // Should be checked because legitimate interest defaults to true and Systems aren't in the fides string
        cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql(expectedTCString);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_2.id]: false,
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: true,
            1: false,
            2: false,
            3: false,
            5: false,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });

    /**
     * TEST CASE #6:
     * ✅ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: ignore all preferences, do not load TCF experience
     */
    it("does nothing when fides_string option when both fides_string option and cookie exist but no experience exists (neither prefetch nor API)", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      setFidesCookie();
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesString: fidesStringOverride,
          },
          experience: OVERRIDE.UNDEFINED,
        },
        OVERRIDE.UNDEFINED,
        OVERRIDE.EMPTY, // return no experience
      );
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    /**
     * TEST CASE #7:
     * ✅ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ✅ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from fides_string option
     */
    it("prefers preferences from fides_string option when both fides_string option and cookie exist and experience is fetched from API", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      setFidesCookie();
      cy.fixture("consent/geolocation_tcf.json").then((geo) => {
        stubTCFExperience({
          stubOptions: { fidesString: fidesStringOverride },
          mockGeolocationApiResp: geo,
        });
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.window().then((win) => {
          win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
        });
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_4.name}`).within(() => {
        // this purpose was previously set to true from the experience, but it is overridden by the fides_string
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_6.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_7.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      cy.get("button").contains("Legitimate interest").click();
      cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      // this purpose is set to true in the experience, but since it was not defined in the fides_string,
      // it should use false as the default
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.get("#fides-panel-vendors").within(() => {
        cy.get("button").contains("Legitimate interest").click();
        cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql(expectedTCString);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_2.id]: false,
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: true,
            1: false,
            2: false,
            3: false,
            5: false,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });

    /**
     * TEST CASE #8:
     * 😬 1) fides_string override option exists but is invalid (via config.options.fidesString)
     * ❌ 2) preferences API (via a custom function)
     * ❌ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ✅ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: ignore invalid fides_string option and render experience as-is
     */
    it("can handle an invalid fides_string option and continue rendering the experience", () => {
      const fidesStringOverride = "invalid-string,2~~dv.";
      cy.fixture("consent/geolocation_tcf.json").then((geo) => {
        stubTCFExperience({
          stubOptions: { fidesString: fidesStringOverride },
          experienceIsInvalid: true,
          mockGeolocationApiResp: geo,
        });
      });

      cy.waitUntilFidesInitialized().then(() => {
        cy.window().then((win) => {
          win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
        });
      });

      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });
      checkDefaultExperienceRender();

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);

          // Make sure our invalid fides string does not make it into tcData
          expect(tcData.tcString).to.be.a("string");
          expect(tcData.tcString).to.not.contain("invalid");
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({});
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });
    /**
     * TEST CASE #9:
     * ✅ 1) fides_string override option (via config.options.fidesString)
     * ✅ 2) preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ✅ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from fides_string option
     */
    it("prefers preferences from fides_string option when fides_string override, custom pref API and cookie exist and experience is fetched from API", () => {
      // This fide str override opts in to all
      const fidesStringOverride =
        "CP0gqMAP0gqMAGXABBENATEIABaAAEAAAAAAABEAAAAA,2~~dv.";
      const fidesString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      setFidesCookie();
      cy.fixture("consent/geolocation_tcf.json").then((geo) => {
        const apiOptions = {
          getPreferencesFn: async () => ({ fides_string: fidesString }),
        };
        const spyObject = cy.spy(apiOptions, "getPreferencesFn");
        stubTCFExperience({
          stubOptions: { apiOptions, fidesString: fidesStringOverride },
          experienceIsInvalid: true,
          mockGeolocationApiResp: geo,
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.window().then((win) => {
            win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
          });
          // eslint-disable-next-line @typescript-eslint/no-unused-expressions
          expect(spyObject).to.be.called;
        });
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_4.name}`).within(() => {
        // this purpose was previously set to true from the experience, but it is overridden by the fides_string
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_6.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_7.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      cy.get("button").contains("Legitimate interest").click();
      cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.get("#fides-panel-vendors").within(() => {
        cy.get("button").contains("Legitimate interest").click();
      });
      // this purpose is set to true in the experience, but since it was not defined in the fides_string,
      // it should use false as the default
      cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql(expectedTCString);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_2.id]: false,
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: true,
            1: false,
            2: false,
            3: false,
            5: false,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });
    /**
     * TEST CASE #10:
     * ❌ 1) fides_string override option (via config.options.fidesString)
     * ✅ 2) preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ✅ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from preferences API, overrides cookie tcf_version_hash if returned in preferences API
     */
    it("prefers preferences from preferences API when custom pref API and cookie exist and experience is fetched from API", () => {
      const fidesString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      const versionHash = "091834y";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      setFidesCookie();
      cy.fixture("consent/geolocation_tcf.json").then((geo) => {
        const apiOptions = {
          getPreferencesFn: async () => ({
            fides_string: fidesString,
            version_hash: versionHash,
          }),
        };
        const spyObject = cy.spy(apiOptions, "getPreferencesFn");
        stubTCFExperience({
          stubOptions: { apiOptions },
          experienceIsInvalid: true,
          mockGeolocationApiResp: geo,
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.window().then((win) => {
            win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
          });
          // eslint-disable-next-line @typescript-eslint/no-unused-expressions
          expect(spyObject).to.be.called;
          // confirm cookie reflects version_hash from custom preferences API
          cy.get("@FidesConsentLoaded")
            .should("have.been.calledOnce")
            .its("firstCall.args.0.detail.tcf_version_hash")
            .should("deep.equal", versionHash);
        });
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_4.name}`).within(() => {
        // this purpose was previously set to true from the experience, but it is overridden by the fides_string
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_6.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_7.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      cy.get("button").contains("Legitimate interest").click();
      cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use false as the default
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      // this purpose is set to true in the experience, but since it was not defined in the fides_string,
      // it should use false as the default
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.get("#fides-panel-vendors").within(() => {
        cy.get("button").contains("Legitimate interest").click();
      });
      cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql(expectedTCString);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_2.id]: false,
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: true,
            1: false,
            2: false,
            3: false,
            5: false,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });
    /**
     * TEST CASE #11:
     * ❌ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ✅ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: prefers preferences from local cookie instead of from client-side experience
     */
    it("prefers preferences from cookie's fides_string when cookie exists and experience is fetched from API", () => {
      setFidesCookie();
      cy.fixture("consent/geolocation_tcf.json").then((geo) => {
        stubTCFExperience({
          stubOptions: { fidesString: undefined },
          experienceIsInvalid: true,
          mockGeolocationApiResp: geo,
        });
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_4.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // also verify that a purpose that was not part of the cookie is also opted out
      // (since it should have no current_preference, and default behavior is opt out)
      cy.getByTestId(`toggle-${PURPOSE_6.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.get("#fides-panel-vendors").within(() => {
        cy.get("button").contains("Legitimate interest").click();
        cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: false,
            2: false,
            1: false,
            3: false,
            5: false,
            8: false,
            9: true,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          const vendorIdOnly = VENDOR_1.id.split(".")[1];
          expect(tcData.vendor.consents).to.eql({
            1: false,
            [vendorIdOnly]: true,
          });
          expect(tcData.vendor.legitimateInterests).to.eql({});
          expect(tcData.specialFeatureOptins).to.eql({
            [SPECIAL_FEATURE_1.id]: true,
          });
        });
    });
    it("can use a fides_string to override a vendor consent", () => {
      // Opts in to all
      const fidesStringOverride =
        "CP0gqMAP0gqMAGXABBENATEIABaAAEAAAAAAABEAAAAA,2~~dv.";
      stubTCFExperience({ stubOptions: { fidesString: fidesStringOverride } });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // Verify the vendor toggle
      // this vendor is set to null in the experience but true in the string
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.vendor.consents).to.eql({
            1: false,
            2: true,
          });
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });
  });

  describe("fides_string override options", () => {
    it("uses fides_string when set via cookie", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      cy.getCookie("fides_string").should("not.exist");
      cy.setCookie("fides_string", fidesStringOverride);
      stubTCFExperience({});
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql(expectedTCString);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_2.id]: false,
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: true,
            1: false,
            2: false,
            3: false,
            5: false,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });

    it("uses fides_string when set via query param", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      cy.getCookie("fides_string").should("not.exist");
      stubTCFExperience({
        demoPageQueryParams: { fides_string: fidesStringOverride },
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql(expectedTCString);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_2.id]: false,
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: true,
            1: false,
            2: false,
            3: false,
            5: false,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });

    it("uses fides_string when set via window obj", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      cy.getCookie("fides_string").should("not.exist");
      stubTCFExperience({
        demoPageWindowParams: { fides_string: fidesStringOverride },
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql(expectedTCString);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_2.id]: false,
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: true,
            1: false,
            2: false,
            3: false,
            5: false,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });

    it("uses fides_string when set via window obj at custom config path", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~~dv.";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA";
      cy.getCookie("fides_string").should("not.exist");
      stubTCFExperience({
        stubOptions: { customOptionsPath: TEST_OVERRIDE_WINDOW_PATH },
        demoPageWindowParams: { fides_string: fidesStringOverride },
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql(expectedTCString);
          expect(tcData.eventStatus).to.eql("cmpuishown");
          expect(tcData.purpose.consents).to.eql({
            [PURPOSE_2.id]: false,
            [PURPOSE_4.id]: false,
            [PURPOSE_6.id]: false,
            [PURPOSE_7.id]: true,
            1: false,
            2: false,
            3: false,
            5: false,
          });
          expect(tcData.purpose.legitimateInterests).to.eql({});
          expect(tcData.vendor.consents).to.eql({});
          expect(tcData.vendor.legitimateInterests).to.eql({});
        });
    });

    it("does not error when window obj at custom config path doesn't exist", () => {
      stubTCFExperience({
        stubOptions: { customOptionsPath: "window.nonexistent_object" },
        demoPageWindowParams: { fides_string: "foo" },
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
        // stubConfig will set window.config.overrides = { fides_string: "foo" }
        expect(win).to.have.nested.property("config.overrides"); // defined by TEST_OVERRIDE_WINDOW_PATH
        // However, customOptionsPath will *try* to read window.nonexistent_object, which will be undefined
        expect(win).not.to.have.property("nonexistent_object");
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql("");
          expect(tcData.eventStatus).to.eql("cmpuishown");
        });
    });

    it("does not error when window obj at nested custom config path doesn't exist", () => {
      stubTCFExperience({
        stubOptions: {
          customOptionsPath: "window.nonexistent_object.nested.path",
        },
        demoPageWindowParams: { fides_string: "foo" },
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
        // stubConfig will set window.config.overrides = { fides_string: "foo" }
        expect(win).to.have.nested.property("config.overrides"); // defined by TEST_OVERRIDE_WINDOW_PATH
        // However, customOptionsPath will *try* to read window.nonexistent_object, which will be undefined
        expect(win).not.to.have.property("nonexistent_object");
      });

      // Open the modal
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });

      // verify CMP API
      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.tcString).to.eql("");
          expect(tcData.eventStatus).to.eql("cmpuishown");
        });
    });
  });

  describe("ac string", () => {
    const AC_IDS = [42, 33, 49];
    const acceptAllAcString = `2~${AC_IDS.sort().join(".")}~dv.`;
    const acceptSomeAcString = `2~33.42~dv.49`;
    const rejectAllAcString = "2~~dv.33.42.49";
    beforeEach(() => {
      cy.fixture("consent/experience_tcf.json").then((payload) => {
        const experience = payload.items[0];
        // Add AC consent only vendors
        const baseVendor = {
          id: "2",
          has_vendor_id: true,
          name: "Test",
          description: "A longer description",
          default_preference: "opt_out",
          purpose_consents: [PURPOSE_4],
        };
        AC_IDS.forEach((id, idx) => {
          const vendor = { ...baseVendor, id: `gacp.${id}`, name: `AC ${id}` };
          experience.tcf_vendor_consents.push({
            ...vendor,
            // Set some of these vendors without purpose_consents
            purpose_consents: idx % 2 === 0 ? [] : baseVendor.purpose_consents,
          });
          experience.tcf_vendor_relationships.push(vendor);
        });
        stubTCFExperience({ experienceFullOverride: experience });
      });
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });
    });

    it("can opt in to all AC vendors and generate string", () => {
      cy.get("#fides-tab-vendors").click();
      AC_IDS.forEach((id) => {
        // Turn all ACs on
        cy.getByTestId(`toggle-AC ${id}`).click();
      });
      cy.get("button").contains("Save").click();
      cy.wait("@patchPrivacyPreference").then((interception) => {
        const { body } = interception.request;
        const expected = [
          { id: VENDOR_1.id, preference: "opt_out" },
          ...AC_IDS.map((id) => ({ id: `gacp.${id}`, preference: "opt_in" })),
        ];
        expect(body.vendor_consent_preferences).to.eql(expected);
        expect(body.method).to.eql(ConsentMethod.SAVE);

        // Check the cookie
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            const { fides_string: tcString } = cookieKeyConsent;
            const acString = tcString?.split(",")[1];
            expect(acString).to.eql(acceptAllAcString);
          });
        });
      });
    });

    it("can opt in to some AC vendors and generate string", () => {
      cy.get("#fides-tab-vendors").click();
      AC_IDS.slice(0, 2).forEach((id) => {
        cy.getByTestId(`toggle-AC ${id}`).click();
      });
      cy.get("button").contains("Save").click();
      cy.wait("@patchPrivacyPreference").then((interception) => {
        const { body } = interception.request;
        const expected = [
          { id: VENDOR_1.id, preference: "opt_out" },
          ...AC_IDS.map((id) => ({
            id: `gacp.${id}`,
            preference: id === 49 ? "opt_out" : "opt_in",
          })),
        ];
        expect(body.vendor_consent_preferences).to.eql(expected);
        expect(body.method).to.eql(ConsentMethod.SAVE);

        // Check the cookie
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            const { fides_string: tcString } = cookieKeyConsent;
            const acString = tcString?.split(",")[1];
            expect(acString).to.eql(acceptSomeAcString);
          });
        });
      });
    });

    it("can opt out of all AC vendors and generate string", () => {
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId("consent-modal").within(() => {
        cy.get("button").contains("Opt out of all").click();
      });
      cy.wait("@patchPrivacyPreference").then((interception) => {
        const { body } = interception.request;
        const expected = [
          { id: VENDOR_1.id, preference: "opt_out" },
          ...AC_IDS.map((id) => ({ id: `gacp.${id}`, preference: "opt_out" })),
        ];
        expect(body.vendor_consent_preferences).to.eql(expected);
        expect(body.method).to.eql(ConsentMethod.REJECT);

        // Check the cookie
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            const { fides_string: tcString } = cookieKeyConsent;
            const acString = tcString?.split(",")[1];
            expect(acString).to.eql(rejectAllAcString);
          });
        });
      });
    });

    it("can emit FidesEvent with composite string but CMP API without", () => {
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId("consent-modal").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });
      cy.wait("@patchPrivacyPreference").then((interception) => {
        expect(interception.request.body.method).to.eql(ConsentMethod.ACCEPT);
      });
      // Both FidesUpdating & FidesUpdated should include the fides_string
      cy.get("@FidesUpdating")
        .should("have.been.calledOnce")
        .its("lastCall.args.0.detail.fides_string")
        .then((fidesString) => {
          const parts = fidesString.split(",");
          expect(parts.length).to.eql(2);
          expect(parts[1]).to.eql(acceptAllAcString);
        });
      cy.get("@FidesUpdated")
        .should("have.been.calledOnce")
        .its("lastCall.args.0.detail.fides_string")
        .then((fidesString) => {
          const parts = fidesString.split(",");
          expect(parts.length).to.eql(2);
          expect(parts[1]).to.eql(acceptAllAcString);
        });

      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.eventStatus).to.eql("useractioncomplete");
          // This fides_string should not be a composite—should just be the tc string
          const { tcString } = tcData;
          const parts = tcString.split(",");
          expect(parts.length).to.eql(1);
          expect(parts[0]).to.not.contain("1~");
          expect(parts[0]).to.not.contain("2~");
          // But we can still access the AC string via `addtlConsent`
          expect(tcData.addtlConsent).to.eql(acceptAllAcString);
        });
    });

    it("can get `addtlConsents` from getTCData custom function", () => {
      cy.get("#fides-tab-vendors").click();
      cy.getByTestId("consent-modal").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });
      cy.wait("@patchPrivacyPreference").then((interception) => {
        expect(interception.request.body.method).to.eql(ConsentMethod.ACCEPT);
      });
      cy.get("@FidesUpdated")
        .should("have.been.calledOnce")
        .its("lastCall.args.0.detail.extraDetails.consentMethod")
        .then((consentMethod) => {
          expect(consentMethod).to.eql(ConsentMethod.ACCEPT);
        });
      // Call getTCData
      cy.window().then((win) => {
        win.__tcfapi("getTCData", 2, cy.stub().as("getTCData"));
        cy.get("@getTCData")
          .should("have.been.calledOnce")
          .its("lastCall.args")
          .then(([tcData, success]) => {
            expect(success).to.eql(true);
            expect(tcData.addtlConsent).to.eql(acceptAllAcString);
          });
      });
    });

    it("can initialize from a v1 AC string", () => {
      const cookie = mockCookie({
        fides_string: "CPzbcgAPzbcgAGXABBENATEIAACAAAAAAAAAABEAAAAA",
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      stubTCFExperience({
        stubOptions: {
          fidesString:
            "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~42.43.44",
        },
      });

      cy.get("@FidesConsentLoaded")
        .should("have.been.calledOnce")
        .its("lastCall.args.0.detail")
        .then((updatedCookie: FidesCookie) => {
          // TC string setting worked
          assertTcOptIns({
            cookie: updatedCookie,
            modelType: "purposeConsents",
            ids: [PURPOSE_7.id],
          });
          // AC string setting worked
          assertAcOptIns({ cookie: updatedCookie, ids: [42, 43, 44] });
        });
    });

    it("can initialize from a v2 AC string", () => {
      const cookie = mockCookie({
        fides_string: "CPzbcgAPzbcgAGXABBENATEIAACAAAAAAAAAABEAAAAA",
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      stubTCFExperience({
        stubOptions: {
          fidesString:
            "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,2~42.43.44~dv.33.49",
        },
      });

      cy.get("@FidesConsentLoaded")
        .should("have.been.calledOnce")
        .its("lastCall.args.0.detail")
        .then((updatedCookie: FidesCookie) => {
          // TC string setting worked
          assertTcOptIns({
            cookie: updatedCookie,
            modelType: "purposeConsents",
            ids: [PURPOSE_7.id],
          });
          // AC string setting worked
          assertAcOptIns({ cookie: updatedCookie, ids: [42, 43, 44] });
        });
    });
  });

  describe("paging", () => {
    const NUM_GVL_VENDORS = 88;
    const NUM_OTHER_VENDORS = 13;
    const GVL_IDS = Array(NUM_GVL_VENDORS)
      .fill(null)
      .map((_, i) => `gvl.${i}`);
    const SYSTEM_IDS = Array(NUM_OTHER_VENDORS)
      .fill(null)
      .map((_, i) => `ctl_${i}`);
    const VENDOR_IDS = [...GVL_IDS, ...SYSTEM_IDS];

    beforeEach(() => {
      cy.fixture("consent/experience_tcf.json").then((payload) => {
        const experience = payload.items[0];
        // Clear out existing data
        experience.tcf_purpose_consents[0].vendors = [];
        experience.tcf_purpose_legitimate_interests[0].vendors = [];
        experience.tcf_purpose_consents[0].systems = [];
        experience.tcf_purpose_legitimate_interests[0].systems = [];
        experience.tcf_features[0].vendors = [];
        experience.tcf_features[0].systems = [];
        experience.tcf_vendor_consents = [];
        experience.tcf_vendor_legitimate_interests = [];
        experience.tcf_vendor_relationships = [];

        // Add lots of vendors so that we can page
        VENDOR_IDS.forEach((id, idx) => {
          const { record, relationship, embedded } = mockTcfVendorObjects({
            id,
            name: `${id} (${idx})`,
          });
          const isGvl = id.indexOf("gvl") > -1;
          if (idx % 2 === 0) {
            // Fill in consents
            experience.tcf_vendor_consents.push(record);
            if (isGvl) {
              experience.tcf_purpose_consents[0].vendors.push(embedded);
            } else {
              experience.tcf_purpose_consents[0].systems.push(embedded);
            }
          } else {
            // Fill in legints
            experience.tcf_vendor_legitimate_interests.push(record);
            if (isGvl) {
              experience.tcf_purpose_legitimate_interests[0].vendors.push(
                embedded,
              );
            } else {
              experience.tcf_purpose_legitimate_interests[0].systems.push(
                embedded,
              );
            }
          }
          // Fill in relationships and purposes
          experience.tcf_vendor_relationships.push(relationship);
          // Fill in features
          if (id.indexOf("gvl") > -1) {
            experience.tcf_features[0].vendors.push(embedded);
          } else {
            experience.tcf_features[0].systems.push(embedded);
          }
          // Also have to add to the gvl obj or else it won't say its an IAB vendor
          if (isGvl) {
            const gvlId = id.split("gvl.")[1];
            experience.gvl.vendors[gvlId] = embedded;
          }
        });
        stubTCFExperience({ experienceFullOverride: experience });
      });
      cy.get("#fides-modal-link").click();
    });

    it("can page through embedded purposes", () => {
      cy.get("#fides-panel-purposes").within(() => {
        cy.get("span").contains(PURPOSE_4.name).click();
        const consentIds = VENDOR_IDS.filter((id, idx) => idx % 2 === 0);
        consentIds.slice(0, 10).forEach((id) => {
          cy.get(".fides-tcf-purpose-vendor-list").contains(id);
        });
        cy.get(".fides-paging-info").contains("1-10 / 51");
        cy.get(".fides-paging-previous-button").should("be.disabled");
        // Go to the next page
        cy.get(".fides-paging-next-button").click();
        cy.get(".fides-paging-info").contains("11-20 / 51");
        consentIds.slice(10, 20).forEach((id) => {
          cy.get(".fides-tcf-purpose-vendor-list").contains(id);
        });
        // Can go back to the previous page
        cy.get(".fides-paging-previous-button").click();
        cy.get(".fides-paging-info").contains("1-10 / 51");
        // Check the last page
        Array(5)
          .fill(null)
          .forEach(() => {
            cy.get(".fides-paging-next-button").click();
          });
        cy.get(".fides-paging-info").contains("51-51 / 51");
        cy.get(".fides-paging-next-button").should("be.disabled");

        // Check legitimate interest
        const legintIds = GVL_IDS.filter((id, idx) => idx % 2 !== 0);
        cy.get("button").contains("Legitimate interest").click();
        cy.get("span").contains(PURPOSE_2.name).click();
        legintIds.slice(0, 10).forEach((id) => {
          cy.get(".fides-tcf-purpose-vendor-list").contains(id);
        });
        // And that paging reset back to 1
        cy.get(".fides-paging-info").contains("1-10 / 50");
      });
    });

    it("can page through features", () => {
      cy.get("#fides-tab-features").click();
      cy.get("#fides-panel-features").within(() => {
        cy.get("span").contains(FEATURE_1.name).click();
        cy.get(".fides-paging-info").contains("1-10 / 101");
        VENDOR_IDS.slice(0, 10).forEach((id) => {
          cy.get(".fides-tcf-purpose-vendor-list").contains(id);
        });
      });
    });

    it("can page through vendors", () => {
      cy.get("#fides-tab-vendors").click();
      cy.get("#fides-panel-vendors").within(() => {
        const consentIds = VENDOR_IDS.filter((id, idx) => idx % 2 === 0);
        consentIds.slice(0, 10).forEach((id) => {
          cy.get(".fides-notice-toggle-title").contains(id);
        });
        cy.get(".fides-record-header").contains("IAB TCF Vendors");
        cy.get(".fides-record-header")
          .contains("Other vendors")
          .should("not.exist");
        cy.get(".fides-paging-info").contains("1-10 / 51");
        cy.get(".fides-paging-next-button").click();
        cy.get(".fides-paging-info").contains("11-20 / 51");
        cy.get(".fides-paging-next-button").click();
        cy.get(".fides-paging-info").contains("21-30 / 51");
        cy.get(".fides-paging-next-button").click();
        cy.get(".fides-paging-info").contains("31-40 / 51");
        // Now go to a page that will show both IAB and other vendors
        cy.get(".fides-paging-next-button").click();
        cy.get(".fides-paging-info").contains("41-50 / 51");
        cy.get(".fides-record-header").contains("IAB TCF Vendors");
        cy.get(".fides-record-header").contains("Other vendors");
        // Last page should only have other vendors
        cy.get(".fides-paging-next-button").click();
        cy.get(".fides-record-header").contains("Other vendors");
        cy.get(".fides-record-header")
          .contains("IAB TCF Vendors")
          .should("not.exist");

        // And spot check legitimate interest
        const legintIds = VENDOR_IDS.filter((id, idx) => idx % 2 !== 0);
        cy.get("button").contains("Legitimate interest").click();
        legintIds.slice(0, 10).forEach((id) => {
          cy.get(".fides-notice-toggle-title").contains(id);
        });
        cy.get(".fides-paging-info").contains("1-10 / 51");
      });
    });
  });

  testCustomPurposes.forEach((includeCustomPurposes) => {
    describe(`Automatically sets preferences ${includeCustomPurposes ? `with` : `without`} custom purposes`, () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubTCFExperience({ includeCustomPurposes });
      });
      describe("Reject all", () => {
        const validateRejectAll = (interception: any) => {
          const { body } = interception.request;
          if (includeCustomPurposes) {
            expect(body.preferences[0].preference).to.eql("opt_out");
            expect(body.preferences[1].preference).to.eql("opt_out");
            expect(body.preferences[2].preference).to.eql("acknowledge"); // notice-only
          }
          // check a few to see they are empty arrays
          expect(body.purpose_consent_preferences).to.eql([]);
          expect(body.purpose_legitimate_interests_preferences).to.eql([]);
          expect(body.method).to.eql(ConsentMethod.SCRIPT);
          cy.get("#fides-banner-container").should("not.exist");
        };
        it("rejects all notices automatically when set", () => {
          stubTCFExperience({
            stubOptions: { fidesConsentOverride: ConsentMethod.REJECT },
            includeCustomPurposes,
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateRejectAll(interception);
            });
          });
        });

        it("rejects all notices automatically when set via cookie", () => {
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          cy.getCookie("fides_consent_override").should("not.exist");
          cy.setCookie("fides_consent_override", ConsentMethod.REJECT);
          stubTCFExperience({ includeCustomPurposes });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateRejectAll(interception);
            });
          });
        });

        it("rejects all notices automatically when set via query param", () => {
          cy.getCookie("fides_string").should("not.exist");
          stubTCFExperience({
            demoPageQueryParams: {
              fides_consent_override: ConsentMethod.REJECT,
            },
            includeCustomPurposes,
          });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateRejectAll(interception);
            });
          });
        });

        it("rejects all notices automatically when set via window obj", () => {
          cy.getCookie("fides_string").should("not.exist");
          stubTCFExperience({
            demoPageWindowParams: {
              fides_consent_override: ConsentMethod.REJECT,
            },
            includeCustomPurposes,
          });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateRejectAll(interception);
            });
          });
        });
      });

      describe("Accept all", () => {
        const validateAcceptAll = (interception: any) => {
          const { body } = interception.request;
          if (includeCustomPurposes) {
            expect(body.preferences[0].preference).to.eql("opt_in");
            expect(body.preferences[1].preference).to.eql("opt_in");
            expect(body.preferences[2].preference).to.eql("acknowledge"); // notice-only
          }
          expect(body.purpose_consent_preferences).to.eql([
            {
              id: 1,
              preference: "opt_in",
            },
            {
              id: 2,
              preference: "opt_in",
            },
            {
              id: 3,
              preference: "opt_in",
            },
            {
              id: 4,
              preference: "opt_in",
            },
            {
              id: 5,
              preference: "opt_in",
            },
            {
              id: 6,
              preference: "opt_in",
            },
            {
              id: 7,
              preference: "opt_in",
            },
            {
              id: 8,
              preference: "opt_in",
            },
            {
              id: 9,
              preference: "opt_in",
            },
            {
              id: 10,
              preference: "opt_in",
            },
            {
              id: 11,
              preference: "opt_in",
            },
          ]);
          expect(body.method).to.eql(ConsentMethod.SCRIPT);
          cy.get("#fides-banner-container").should("not.exist");
        };
        it("accepts all notices automatically when set", () => {
          stubTCFExperience({
            stubOptions: { fidesConsentOverride: ConsentMethod.ACCEPT },
            includeCustomPurposes,
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateAcceptAll(interception);
            });
          });
        });

        it("accepts all notices automatically when set via cookie", () => {
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          cy.getCookie("fides_consent_override").should("not.exist");
          cy.setCookie("fides_consent_override", ConsentMethod.ACCEPT);
          stubTCFExperience({ includeCustomPurposes });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateAcceptAll(interception);
            });
          });
        });

        it("accepts all notices automatically when set via query param", () => {
          cy.getCookie("fides_string").should("not.exist");
          stubTCFExperience({
            demoPageQueryParams: {
              fides_consent_override: ConsentMethod.ACCEPT,
            },
            includeCustomPurposes,
          });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateAcceptAll(interception);
            });
          });
        });

        it("accepts all notices automatically when set via window obj", () => {
          cy.getCookie("fides_string").should("not.exist");
          stubTCFExperience({
            demoPageWindowParams: {
              fides_consent_override: ConsentMethod.ACCEPT,
            },
            includeCustomPurposes,
          });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateAcceptAll(interception);
            });
          });
        });
      });
    });
  });

  describe("Legacy event support", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    });

    it("dispatches FidesInitialized at FidesConsentLoaded time when fides_initialized_event_mode is 'multiple'", () => {
      // Set up a cookie so that FidesConsentLoaded will be dispatched
      const cookie = mockCookie({
        tcf_version_hash: TCF_VERSION_HASH,
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));

      // Enable legacy event support
      stubTCFExperience({
        stubOptions: { fidesInitializedEventMode: "multiple" },
      });

      cy.waitUntilFidesInitialized().then(() => {
        // Verify that FidesInitialized was dispatched twice:
        // 1. At FidesConsentLoaded time (legacy behavior)
        // 2. At FidesReady time (normal behavior)
        cy.get("@dataLayerPush")
          .should("have.been.callCount", 4) // FidesConsentLoaded + FidesInitialized (legacy) + FidesReady + FidesInitialized (normal)
          .its("args")
          .then((args) => {
            // First call should be FidesConsentLoaded
            const firstCall = args[0][0];
            expect(firstCall.event).to.equal("FidesConsentLoaded");

            // Second call should be FidesInitialized (legacy)
            const secondCall = args[1][0];
            expect(secondCall.event).to.equal("FidesInitialized");

            // Third call should be FidesReady
            const thirdCall = args[2][0];
            expect(thirdCall.event).to.equal("FidesReady");

            // Fourth call should be FidesInitialized (normal)
            const fourthCall = args[3][0];
            expect(fourthCall.event).to.equal("FidesInitialized");
          });
      });
    });

    it("does not dispatch FidesInitialized at FidesConsentLoaded time when fides_initialized_event_mode is 'once'", () => {
      // Set up a cookie so that FidesConsentLoaded will be dispatched
      const cookie = mockCookie({
        tcf_version_hash: TCF_VERSION_HASH,
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));

      // Do not enable legacy event support
      stubTCFExperience({});

      cy.waitUntilFidesInitialized().then(() => {
        // Verify that FidesInitialized was only dispatched once at FidesReady time
        cy.get("@dataLayerPush")
          .should("have.been.callCount", 3) // FidesConsentLoaded + FidesReady + FidesInitialized (normal)
          .its("args")
          .then((args) => {
            // First call should be FidesConsentLoaded
            const firstCall = args[0][0];
            expect(firstCall.event).to.equal("FidesConsentLoaded");

            // Second call should be FidesReady
            const secondCall = args[1][0];
            expect(secondCall.event).to.equal("FidesReady");

            // Third call should be FidesInitialized (normal)
            const thirdCall = args[2][0];
            expect(thirdCall.event).to.equal("FidesInitialized");

            // Should only have one FidesInitialized event (no legacy one)
            const fidesInitializedEvents = args.filter(
              ([event]) => event.event === "FidesInitialized",
            );
            expect(fidesInitializedEvents).to.have.length(1);
          });
      });
    });

    it("supports fides_initialized_event_mode via query param", () => {
      // Set up a cookie so that FidesConsentLoaded will be dispatched
      const cookie = mockCookie({
        tcf_version_hash: TCF_VERSION_HASH,
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));

      // Enable legacy event support via query param
      stubTCFExperience({
        demoPageQueryParams: { fides_initialized_event_mode: "multiple" },
      });

      cy.waitUntilFidesInitialized().then(() => {
        // Verify that FidesInitialized was dispatched at FidesConsentLoaded time (legacy) and FidesReady time (normal)
        cy.get("@dataLayerPush")
          .its("args")
          .then((args) => {
            const fidesInitializedEvents = args.filter(
              ([event]) => event.event === "FidesInitialized",
            );
            expect(fidesInitializedEvents).to.have.length(2);

            // The first FidesInitialized event should come after FidesConsentLoaded (legacy)
            const firstCall = args[0][0];
            const secondCall = args[1][0];
            expect(firstCall.event).to.equal("FidesConsentLoaded");
            expect(secondCall.event).to.equal("FidesInitialized");
          });
      });
    });

    it("supports fides_initialized_event_mode via window object", () => {
      // Set up a cookie so that FidesConsentLoaded will be dispatched
      const cookie = mockCookie({
        tcf_version_hash: TCF_VERSION_HASH,
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));

      // Enable legacy event support via window object
      stubTCFExperience({
        demoPageWindowParams: { fides_initialized_event_mode: "multiple" },
      });

      cy.waitUntilFidesInitialized().then(() => {
        // Verify that FidesInitialized was dispatched at FidesConsentLoaded time (legacy) and FidesReady time (normal)
        cy.get("@dataLayerPush")
          .its("args")
          .then((args) => {
            const fidesInitializedEvents = args.filter(
              ([event]) => event.event === "FidesInitialized",
            );
            expect(fidesInitializedEvents).to.have.length(2);

            // The first FidesInitialized event should come after FidesConsentLoaded (legacy)
            const firstCall = args[0][0];
            const secondCall = args[1][0];
            expect(firstCall.event).to.equal("FidesConsentLoaded");
            expect(secondCall.event).to.equal("FidesInitialized");
          });
      });
    });
  });
});
