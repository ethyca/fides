/* eslint-disable no-underscore-dangle */
import {
  CONSENT_COOKIE_NAME,
  FidesCookie,
  PrivacyExperience,
  UserConsentPreference,
} from "fides-js";
import { stubConfig } from "../support/stubs";

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
  id: "2",
  name: "Captify",
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

describe("Fides-js TCF", () => {
  beforeEach(() => {
    cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    cy.fixture("consent/experience_tcf.json").then((experience) => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
          tcfEnabled: true,
        },
        experience: experience.items[0],
      });
    });
  });

  describe("banner appears when it should", () => {
    const setAllTcfToValue = (
      experience: PrivacyExperience,
      value: UserConsentPreference | undefined
    ): PrivacyExperience => {
      const consentPurposes = experience.tcf_purpose_consents?.map((p) => ({
        ...p,
        current_preference: value,
      }));
      const legintPurposes = experience.tcf_purpose_legitimate_interests?.map(
        (p) => ({ ...p, current_preference: value })
      );
      const specialPurposes = experience.tcf_special_purposes?.map((p) => ({
        ...p,
        current_preference: value,
      }));
      const features = experience.tcf_features?.map((f) => ({
        ...f,
        current_preference: value,
      }));
      const specialFeatures = experience.tcf_special_features?.map((f) => ({
        ...f,
        current_preference: value,
      }));
      const consentVendors = experience.tcf_vendor_consents?.map((v) => ({
        ...v,
        current_preference: value,
      }));
      const legintVendors = experience.tcf_vendor_legitimate_interests?.map(
        (v) => ({
          ...v,
          current_preference: value,
        })
      );
      const consentSystems = experience.tcf_system_consents?.map((s) => ({
        ...s,
        current_preference: value,
      }));
      const legintSystems = experience.tcf_system_legitimate_interests?.map(
        (v) => ({
          ...v,
          current_preference: value,
        })
      );
      return {
        ...experience,
        tcf_purpose_consents: consentPurposes,
        tcf_purpose_legitimate_interests: legintPurposes,
        tcf_special_purposes: specialPurposes,
        tcf_features: features,
        tcf_special_features: specialFeatures,
        tcf_vendor_consents: consentVendors,
        tcf_vendor_legitimate_interests: legintVendors,
        tcf_system_consents: consentSystems,
        tcf_system_legitimate_interests: legintSystems,
      };
    };
    it("banner should not appear if everything already has a preference", () => {
      cy.fixture("consent/experience_tcf.json").then((payload) => {
        const experience = payload.items[0];
        const updatedExperience = setAllTcfToValue(
          experience,
          UserConsentPreference.OPT_IN
        );
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
          },
          experience: updatedExperience,
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });
    });
    it("should render the banner if there is even one preference that is not set", () => {
      cy.fixture("consent/experience_tcf.json").then((payload) => {
        const experience = payload.items[0];
        const updatedExperience = setAllTcfToValue(
          experience,
          UserConsentPreference.OPT_IN
        );
        updatedExperience.tcf_purpose_consents![0].current_preference =
          undefined;
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
          },
          experience: updatedExperience,
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner");
        });
      });
    });
  });

  describe("initial layer", () => {
    it("can render purposes in the initial layer as a stack", () => {
      cy.get("div#fides-banner").within(() => {
        cy.get("span").contains(STACK_1.name);
        cy.get("span").contains(PURPOSE_6.name);

        cy.get("span").contains(STACK_1.name).click();
        [PURPOSE_4.id, PURPOSE_9.id, PURPOSE_7.id, PURPOSE_2.id].forEach(
          (id) => {
            cy.get("li").contains(`Purpose ${id}`);
          }
        );
      });
    });

    it("can open the modal", () => {
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });
      cy.get("#fides-tab-Purposes");
    });

    it("can open the modal from vendor information", () => {
      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Vendors").click();
      });
      cy.get("#fides-tab-Vendors");
      cy.getByTestId(`toggle-${SYSTEM_1.name}`);
      cy.getByTestId(`toggle-${VENDOR_1.name}-consent`);
    });
  });

  describe("second layer", () => {
    beforeEach(() => {
      cy.get("#fides-modal-link").click();
    });

    describe("rendering the TCF modal", () => {
      it("can render tabs", () => {
        cy.get("#fides-tab-Purposes");
        // Purposes
        cy.getByTestId("toggle-Purposes").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_9.name}-consent`).within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
        cy.get(".fides-notice-toggle-header").contains("Special purposes");
        cy.get(".fides-notice-toggle-title").contains(SPECIAL_PURPOSE_1.name);
        cy.getByTestId("toggle-Special purposes").should("not.exist");
        cy.getByTestId(`toggle-${SPECIAL_PURPOSE_1.name}`).should("not.exist");

        cy.get("#fides-tab-Features").click();
        cy.get(".fides-notice-toggle-header").contains("Features");
        cy.get(".fides-notice-toggle-title").contains(FEATURE_1.name);
        cy.get(".fides-notice-toggle-title").contains(FEATURE_2.name);
        cy.getByTestId(`toggle-${FEATURE_1.name}`).should("not.exist");
        cy.getByTestId(`toggle-${FEATURE_2.name}`).should("not.exist");
        cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });

        // Vendors
        cy.get("#fides-tab-Vendors").click();
        cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
      });

      it("can render IAB TCF badge on vendors and filter", () => {
        const newVendor = {
          // Use the new vendor id scheme
          id: "gvl.1",
          name: "Exponential Interactive, Inc d/b/a VDX.tv",
        };
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience = payload.items[0];
          experience.tcf_vendor_consents.push(newVendor);
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience,
          });
        });
        cy.get("#fides-modal-link").click();
        cy.get("#fides-tab-Vendors").click();
        cy.get("span")
          .contains(SYSTEM_1.name)
          .within(() => {
            cy.get("span").should("not.exist");
          });
        cy.get("span")
          .contains(VENDOR_1.name)
          .within(() => {
            cy.get("span").contains("IAB TCF");
          });
        cy.get("span")
          .contains(newVendor.name)
          .within(() => {
            cy.get("span").contains("IAB TCF");
          });

        // Filter to just GVL
        cy.get(".fides-filter-button-group").within(() => {
          cy.get("button").contains("IAB TCF vendors").click();
        });
        cy.get("span").contains(SYSTEM_1.name).should("not.exist");
        cy.get("span").contains(VENDOR_1.name);
        cy.get("span").contains(newVendor.name);

        // Check that the vendor ids persisted to the TC string
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        cy.window().then((win) => {
          win.__tcfapi("getTCData", 2, cy.stub().as("getTCData"));
        });
        cy.get("@getTCData")
          .should("have.been.calledOnce")
          .its("lastCall.args")
          .then(([tcData, success]) => {
            expect(success).to.eql(true);
            expect(tcData.vendor.consents).to.eql({ 1: true, 2: true });
          });
      });

      it("can group toggle", () => {
        // Toggle just legitimate interests
        cy.getByTestId("toggle-Purposes").click();
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });

        // Toggle a child back on
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).click();
        cy.getByTestId("toggle-Purposes").within(() => {
          cy.get("input").should("be.checked");
        });

        // Do the same for consent column
        cy.getByTestId("toggle-all-Purposes-consent").click();
        cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        // Toggle back on
        cy.getByTestId("toggle-all-Purposes-consent").click();
        cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
          cy.get("input").should("be.checked");
        });

        // Try the all on/all off button
        cy.get("button").contains("All off").click();
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
          cy.get("input").should("not.be.checked");
        });
      });

      it("can handle group toggle empty states", () => {
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience = payload.items[0];
          const updatedExperience = { ...experience, tcf_purpose_consents: [] };
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience: updatedExperience,
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.get("#fides-modal-link").click();
            cy.getByTestId(`toggle-all-Purposes-consent`).should("not.exist");
          });
        });
      });

      it("can handle all on/all off empty states", () => {
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience = payload.items[0];
          const updatedExperience = {
            ...experience,
            tcf_purpose_consents: [],
            tcf_purpose_legitimate_interests: [],
          };
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience: updatedExperience,
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.get("#fides-modal-link").click();
            // Should not show up on the purpose tab
            cy.get(".fides-all-on-off-buttons").should("not.be.visible");
            // But should show up in Features
            cy.get("#fides-tab-Features").click();
            cy.get(".fides-all-on-off-buttons").should("be.visible");
          });
        });
      });

      it("can toggle double toggles individually", () => {
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience = payload.items[0];
          // Add a vendor legitimate interest which is the same as vendor consent
          // eslint-disable-next-line @typescript-eslint/naming-convention
          const tcf_vendor_legitimate_interests = [
            {
              ...experience.tcf_vendor_consents[0],
              default_preference: "opt_in",
              purpose_legitimate_interests: [PURPOSE_2.id],
            },
          ];
          const updatedExperience = {
            ...experience,
            tcf_vendor_legitimate_interests,
          };
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience: updatedExperience,
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.get("#fides-modal-link").click();
            cy.get("#fides-tab-Vendors").click();
            cy.getByTestId(`toggle-${VENDOR_1.name}`).click();
            cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
              cy.get("input").should("not.be.checked");
            });
            cy.getByTestId(`toggle-${VENDOR_1.name}-consent`).within(() => {
              cy.get("input").should("not.be.checked");
            });
          });
        });
      });
    });

    describe("saving preferences", () => {
      const expectedEndOfFidesString = ".IABE,1~";
      it("can opt in to all", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_consent_preferences).to.eql([
              { id: PURPOSE_4.id, preference: "opt_in" },
              { id: PURPOSE_6.id, preference: "opt_in" },
              { id: PURPOSE_7.id, preference: "opt_in" },
              { id: PURPOSE_9.id, preference: "opt_in" },
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
              { id: VENDOR_1.id, preference: "opt_in" },
            ]);
            expect(body.vendor_legitimate_interests_preferences).to.eql([]);
            expect(body.system_legitimate_interests_preferences).to.eql([
              { id: SYSTEM_1.id, preference: "opt_in" },
            ]);
            expect(body.system_consent_preferences).to.eql([]);
          });
        });
        // Verify the cookie on save
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          [PURPOSE_9.id, PURPOSE_6.id, PURPOSE_7.id, PURPOSE_4.id].forEach(
            (pid) => {
              expect(cookieKeyConsent.tcf_consent.purpose_consent_preferences)
                .property(`${pid}`)
                .is.eql(true);
            }
          );
          expect(
            cookieKeyConsent.tcf_consent
              .purpose_legitimate_interests_preferences
          )
            .property(`${PURPOSE_2.id}`)
            .is.eql(true);
          expect(cookieKeyConsent.tcf_consent.special_feature_preferences)
            .property(`${SPECIAL_FEATURE_1.id}`)
            .is.eql(true);
          expect(cookieKeyConsent.tcf_consent.vendor_consent_preferences)
            .property(`${VENDOR_1.id}`)
            .is.eql(true);
          expect(
            cookieKeyConsent.tcf_consent.vendor_legitimate_interests_preferences
          ).to.eql({});
          expect(
            cookieKeyConsent.tcf_consent.system_consent_preferences
          ).to.eql({});
          expect(
            cookieKeyConsent.tcf_consent.system_legitimate_interests_preferences
          )
            .property(`${SYSTEM_1.id}`)
            .is.eql(true);

          // Confirm vendors_disclosed section
          expect(
            cookieKeyConsent.fides_tc_string?.endsWith(expectedEndOfFidesString)
          ).to.eql(true);
        });
      });

      it("can opt out of all", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt out of all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_consent_preferences).to.eql([
              { id: PURPOSE_4.id, preference: "opt_out" },
              { id: PURPOSE_6.id, preference: "opt_out" },
              { id: PURPOSE_7.id, preference: "opt_out" },
              { id: PURPOSE_9.id, preference: "opt_out" },
            ]);
            expect(body.purpose_legitimate_interests_preferences).to.eql([
              { id: PURPOSE_2.id, preference: "opt_out" },
            ]);
            expect(body.special_purpose_preferences).to.eql(undefined);
            expect(body.feature_preferences).to.eql(undefined);
            expect(body.special_feature_preferences).to.eql([
              { id: SPECIAL_FEATURE_1.id, preference: "opt_out" },
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
        });
        // Verify the cookie on save
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          [PURPOSE_4.id, PURPOSE_9.id, PURPOSE_6.id, PURPOSE_7.id].forEach(
            (pid) => {
              expect(cookieKeyConsent.tcf_consent.purpose_consent_preferences)
                .property(`${pid}`)
                .is.eql(false);
            }
          );
          expect(
            cookieKeyConsent.tcf_consent
              .purpose_legitimate_interests_preferences
          )
            .property(`${PURPOSE_2.id}`)
            .is.eql(false);
          expect(cookieKeyConsent.tcf_consent.special_feature_preferences)
            .property(`${SPECIAL_FEATURE_1.id}`)
            .is.eql(false);
          expect(cookieKeyConsent.tcf_consent.vendor_consent_preferences)
            .property(`${VENDOR_1.id}`)
            .is.eql(false);
          expect(
            cookieKeyConsent.tcf_consent.vendor_legitimate_interests_preferences
          ).to.eql({});
          expect(
            cookieKeyConsent.tcf_consent.system_consent_preferences
          ).to.eql({});
          expect(
            cookieKeyConsent.tcf_consent.system_legitimate_interests_preferences
          )
            .property(`${SYSTEM_1.id}`)
            .is.eql(false);
          // Confirm vendors_disclosed section
          expect(
            cookieKeyConsent.fides_tc_string?.endsWith(expectedEndOfFidesString)
          ).to.eql(true);
        });
      });

      it("can opt in to some and opt out of others", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).click();
          cy.get("#fides-tab-Features").click();
          cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).click();

          cy.get("#fides-tab-Vendors").click();
          cy.getByTestId(`toggle-${SYSTEM_1.name}`).click();
          cy.get("button").contains("Save").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_consent_preferences).to.eql([
              { id: PURPOSE_4.id, preference: "opt_out" },
              { id: PURPOSE_6.id, preference: "opt_in" },
              { id: PURPOSE_7.id, preference: "opt_in" },
              { id: PURPOSE_9.id, preference: "opt_in" },
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
        });
        // Verify the cookie on save
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          [PURPOSE_9.id, PURPOSE_6.id, PURPOSE_7.id].forEach((pid) => {
            expect(cookieKeyConsent.tcf_consent.purpose_consent_preferences)
              .property(`${pid}`)
              .is.eql(true);
          });
          expect(
            cookieKeyConsent.tcf_consent
              .purpose_legitimate_interests_preferences
          )
            .property(`${PURPOSE_2.id}`)
            .is.eql(true);
          expect(cookieKeyConsent.tcf_consent.purpose_consent_preferences)
            .property(`${PURPOSE_4.id}`)
            .is.eql(false);
          expect(cookieKeyConsent.tcf_consent.special_feature_preferences)
            .property(`${SPECIAL_FEATURE_1.id}`)
            .is.eql(true);
          expect(cookieKeyConsent.tcf_consent.vendor_consent_preferences)
            .property(`${VENDOR_1.id}`)
            .is.eql(false);
          expect(
            cookieKeyConsent.tcf_consent.vendor_legitimate_interests_preferences
          ).to.eql({});
          expect(
            cookieKeyConsent.tcf_consent.system_legitimate_interests_preferences
          )
            .property(`${SYSTEM_1.id}`)
            .is.eql(false);
          expect(
            cookieKeyConsent.tcf_consent.system_consent_preferences
          ).to.eql({});
          // Confirm vendors_disclosed section
          expect(
            cookieKeyConsent.fides_tc_string?.endsWith(expectedEndOfFidesString)
          ).to.eql(true);
        });
      });
    });
  });

  describe("cmp api", () => {
    beforeEach(() => {
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      cy.get("#fides-modal-link").click();
    });

    it("can receive a cmpuishown event", () => {
      cy.get("@TCFEvent")
        .its("firstCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.eventStatus === "cmpuishown");
        });
    });

    describe("setting fields", () => {
      it("can opt in to all and set legitimate interests", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
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
            expect(tcData.vendor.consents).to.eql({
              1: false,
              [VENDOR_1.id]: true,
            });
            expect(tcData.vendor.legitimateInterests).to.eql({});
          });
      });

      it("can handle inappropriate legint purposes", () => {
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience: PrivacyExperience = payload.items[0];
          // Set purpose with id 4 to LegInt which is not allowed!
          const purpose4 = experience.tcf_purpose_consents?.find(
            (p) => p.id === 4
          )!;
          experience.tcf_purpose_legitimate_interests?.push(purpose4);
          // Set the corresponding embedded vendor purpose too
          const vendor = experience.tcf_purpose_consents![0];
          experience.tcf_vendor_legitimate_interests?.push({
            ...vendor,
            id: "test",
            purpose_legitimate_interests: [{ id: 4, name: purpose4.name }],
          });

          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience,
          });
        });
        // Since we've changed windows, redeclare the stub too
        cy.window().then((win) => {
          win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent2"));
        });
        cy.get("#fides-modal-link").click();
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
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
            expect(tcData.vendor.consents).to.eql({
              1: false,
              [VENDOR_1.id]: true,
            });
            expect(tcData.vendor.legitimateInterests).to.eql({});
          });
      });
    });
  });

  describe("cookie interactions", () => {
    it("can initialize preferences from a cookie", () => {
      /**
       * The default from the fixture is that
       *   - all purposes are opted in
       *   - all special purposes are opted in
       *   - feature 1 is opted out, feature 2 has no preference
       *   - all vendors are opted in
       *   - all systems are opted in
       *
       * We'll change at least one value from each entity type in the cookie
       */
      const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
      const CREATED_DATE = "2022-12-24T12:00:00.000Z";
      const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
      const cookie = {
        identity: { fides_user_device_id: uuid },
        fides_meta: {
          version: "0.9.0",
          createdAt: CREATED_DATE,
          updatedAt: UPDATED_DATE,
        },
        consent: {},
        tcf_consent: {
          purpose_consent_preferences: {
            [PURPOSE_4.id]: false,
            [PURPOSE_9.id]: true,
          },
          special_feature_preferences: { [SPECIAL_FEATURE_1.id]: true },
          system_legitimate_interests_preferences: { [SYSTEM_1.id]: false },
          vendor_consent_preferences: { [VENDOR_1.id]: true },
        },
      };
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
          },
          experience: experience.items[0],
        });
      });
      // Open the modal
      cy.get("#fides-modal-link").click();

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}-consent`).within(() => {
        cy.get("input").should("be.checked");
      });
      // also verify that a purpose that was not part of the cookie is also opted out
      // (since it should have no current_preference, and default behavior is opt out)
      cy.getByTestId(`toggle-${PURPOSE_6.name}-consent`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-Features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      cy.get("#fides-tab-Vendors").click();
      cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${VENDOR_1.name}-consent`).within(() => {
        cy.get("input").should("be.checked");
      });
    });
  });

  describe("ac string", () => {
    const AC_IDS = [42, 33, 49];
    const acceptAllAcString = `1~${AC_IDS.sort().join(".")}`;
    const rejectAllAcString = "1~";
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
          current_preference: null,
          outdated_preference: null,
          current_served: null,
          outdated_served: null,
          purpose_consents: [
            {
              id: 4,
              name: "Use profiles to select personalised advertising",
            },
          ],
        };
        AC_IDS.forEach((id, idx) => {
          experience.tcf_vendor_consents.push({
            ...baseVendor,
            id: `ac.${id}`,
            name: `AC ${id}`,
            // Set some of these vendors without purpose_consents
            purpose_consents: idx % 2 === 0 ? [] : baseVendor.purpose_consents,
          });
        });

        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
          },
          experience,
        });
      });
      cy.get("#fides-modal-link").click();
    });

    it("can opt in to AC vendors and generate string", () => {
      cy.get("#fides-tab-Vendors").click();
      AC_IDS.forEach((id) => {
        cy.getByTestId(`toggle-AC ${id}-consent`);
      });
      cy.get("section#fides-panel-Vendors").within(() => {
        cy.get("button").contains("All on").click();
      });
      cy.get("button").contains("Save").click();
      cy.wait("@patchPrivacyPreference").then((interception) => {
        const { body } = interception.request;
        const expected = [
          { id: VENDOR_1.id, preference: "opt_in" },
          ...AC_IDS.map((id) => ({ id: `ac.${id}`, preference: "opt_in" })),
        ];
        expect(body.vendor_consent_preferences).to.eql(expected);

        // Check the cookie
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          const { fides_tc_string: tcString } = cookieKeyConsent;
          const acString = tcString?.split(",")[1];
          expect(acString).to.eql(acceptAllAcString);
        });
      });
    });

    it("can opt out of AC vendors and generate string", () => {
      cy.get("#fides-tab-Vendors").click();
      cy.get("section#fides-panel-Vendors").within(() => {
        cy.get("button").contains("All off").click();
      });
      cy.get("button").contains("Save").click();
      cy.wait("@patchPrivacyPreference").then((interception) => {
        const { body } = interception.request;
        const expected = [
          { id: VENDOR_1.id, preference: "opt_out" },
          ...AC_IDS.map((id) => ({ id: `ac.${id}`, preference: "opt_out" })),
        ];
        expect(body.vendor_consent_preferences).to.eql(expected);

        // Check the cookie
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          const { fides_tc_string: tcString } = cookieKeyConsent;
          const acString = tcString?.split(",")[1];
          expect(acString).to.eql(rejectAllAcString);
        });
      });
    });

    it("can emit FidesEvent with composite string but CMP API without", () => {
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      cy.get("#fides-tab-Vendors").click();
      cy.get("section#fides-panel-Vendors").within(() => {
        cy.get("button").contains("All on").click();
      });
      cy.get("button").contains("Save").click();
      cy.wait("@patchPrivacyPreference");
      cy.get("@FidesUpdated")
        .should("have.been.calledTwice")
        .its("secondCall.args.0.detail.fides_tc_string")
        .then((fidesTcString) => {
          const parts = fidesTcString.split(",");
          expect(parts.length).to.eql(2);
          expect(parts[1]).to.eql(acceptAllAcString);
        });

      cy.get("@TCFEvent")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.eventStatus).to.eql("useractioncomplete");
          // This TC string should not be a composite—should just be the tc string
          const { tcString } = tcData;
          const parts = tcString.split(",");
          expect(parts.length).to.eql(1);
          expect(parts[0]).to.not.contain("1~");
          // But we can still access the AC string via `addtlConsent`
          expect(tcData.addtlConsent).to.eql(acceptAllAcString);
        });
    });

    it("can get `addtlConsents` from getTCData custom function", () => {
      cy.get("#fides-tab-Vendors").click();
      cy.get("section#fides-panel-Vendors").within(() => {
        cy.get("button").contains("All on").click();
      });
      cy.get("button").contains("Save").click();
      cy.wait("@patchPrivacyPreference");
      // Call getTCData
      cy.window().then((win) => {
        win.__tcfapi("getTCData", 2, cy.stub().as("getTCData"));
      });
      cy.get("@getTCData")
        .should("have.been.calledOnce")
        .its("lastCall.args")
        .then(([tcData, success]) => {
          expect(success).to.eql(true);
          expect(tcData.addtlConsent).to.eql(acceptAllAcString);
        });
    });
  });
});
