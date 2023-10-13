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

        // Filter to just GVL
        cy.get(".fides-filter-button-group").within(() => {
          cy.get("button").contains("IAB TCF vendors").click();
        });
        cy.get("span").contains(SYSTEM_1.name).should("not.exist");
        cy.get("span").contains(VENDOR_1.name);
      });

      it("can group toggle and fire FidesUIChanged events", () => {
        // Toggle just legitimate interests
        cy.getByTestId("toggle-Purposes").click();
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.get("@FidesUIChanged").its("callCount").should("equal", 1);

        // Toggle a child back on
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).click();
        cy.getByTestId("toggle-Purposes").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.get("@FidesUIChanged").its("callCount").should("equal", 2);

        // Do the same for consent column
        cy.getByTestId("toggle-all-Purposes-consent").click();
        cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.get("@FidesUIChanged").its("callCount").should("equal", 3);
        // Toggle back on
        cy.getByTestId("toggle-all-Purposes-consent").click();
        cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
          cy.get("input").should("be.checked");
        });
        cy.get("@FidesUIChanged").its("callCount").should("equal", 4);

        // Try the all on/all off button
        cy.get("button").contains("All off").click();
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.get("@FidesUIChanged").its("callCount").should("equal", 5);
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
            cy.get("@FidesUIChanged").should("have.been.calledOnce");
          });
        });
      });
    });

    describe("saving preferences", () => {
      it("can opt in to all", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            cy.get("@FidesUIChanged").should("not.have.been.called");
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
        });
      });

      it("can opt out of all", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt out of all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            cy.get("@FidesUIChanged").should("not.have.been.called");
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
          cy.get("@FidesUIChanged").its("callCount").should("equal", 3);
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
});
