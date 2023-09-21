/* eslint-disable no-underscore-dangle */
import {
  CONSENT_COOKIE_NAME,
  FidesCookie,
  PrivacyExperience,
  UserConsentPreference,
} from "fides-js";
import { stubConfig } from "../support/stubs";

const PURPOSE_1 = {
  id: 4,
  name: "Use profiles to select personalised advertising",
};
const PURPOSE_2 = {
  id: 9,
  name: "Understand audiences through statistics or combinations of data from different sources",
};
const PURPOSE_3 = {
  id: 6,
  name: "Use profiles to select personalised content",
};
const PURPOSE_4 = {
  id: 7,
  name: "Measure advertising performance",
};
const PURPOSE_5 = {
  id: 2,
  name: "Use limited data to select advertising",
};
const SPECIAL_PURPOSE_1 = {
  id: 1,
  name: "Ensure security, prevent and detect fraud, and fix errors",
};
const VENDOR_1 = {
  id: "Fides System",
  name: "Fides System",
};
const VENDOR_2 = {
  id: "2",
  name: "amplitude",
};
const STACK_1 = {
  id: 7,
  name: "Selection of personalised advertising, advertising measurement, and audience research",
};
const FEATURE_1 = {
  id: 1,
  name: "Match and combine offline data sources",
};
const FEATURE_2 = {
  id: 2,
  name: "Link different devices",
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
      const purposes = experience.tcf_purposes?.map((p) => ({
        ...p,
        current_preference: value,
      }));
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
      const vendors = experience.tcf_vendors?.map((v) => ({
        ...v,
        current_preference: value,
      }));
      const systems = experience.tcf_systems?.map((s) => ({
        ...s,
        current_preference: value,
      }));
      return {
        ...experience,
        tcf_purposes: purposes,
        tcf_special_purposes: specialPurposes,
        tcf_features: features,
        tcf_special_features: specialFeatures,
        tcf_vendors: vendors,
        tcf_systems: systems,
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
        updatedExperience.tcf_purposes![0].current_preference = undefined;
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
    beforeEach(() => {
      cy.get("#fides-modal-link").click();
    });

    it("can render purposes in the initial layer as a stack", () => {
      cy.get("span").contains(STACK_1.name);
      cy.get("span").contains(PURPOSE_3.name);

      cy.get("span").contains(STACK_1.name).click();
      [PURPOSE_1.id, PURPOSE_2.id, PURPOSE_4.id, PURPOSE_5.id].forEach((id) => {
        cy.get("li").contains(`Purpose ${id}`);
      });
    });
  });

  describe("second layer", () => {
    beforeEach(() => {
      cy.get("#fides-modal-link").click();
      cy.getByTestId("fides-modal-content").within(() => {
        cy.get("#fides-banner-button-secondary")
          .contains("Manage preferences")
          .click();
      });
    });

    describe("rendering the TCF modal", () => {
      it("can render tabs", () => {
        cy.get("#fides-tab-Purposes");
        // Purposes
        cy.getByTestId("toggle-Purposes").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_1.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Special purposes").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId(`toggle-${SPECIAL_PURPOSE_1.name}`).within(() => {
          cy.get("input").should("be.checked");
        });

        cy.get("#fides-tab-Features").click();
        cy.getByTestId(`toggle-${FEATURE_1.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId(`toggle-${FEATURE_2.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });

        // Vendors
        cy.get("#fides-tab-Vendors").click();
        cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
          cy.get("input").should("be.checked");
        });
      });

      it("can render GVL badge on vendors and filter", () => {
        cy.get("#fides-tab-Vendors").click();
        cy.get("span")
          .contains(VENDOR_1.name)
          .within(() => {
            cy.get("span").should("not.exist");
          });
        cy.get("span")
          .contains(VENDOR_2.name)
          .within(() => {
            cy.get("span").contains("GVL");
          });

        // Filter to just GVL
        cy.get(".fides-filter-button-group").within(() => {
          cy.get("button").contains("GVL vendors").click();
        });
        cy.get("span").contains(VENDOR_1.name).should("not.exist");
        cy.get("span").contains(VENDOR_2.name);
      });

      it("can filter by legal bases", () => {
        // Purposes tab
        cy.getByTestId(`toggle-${PURPOSE_1.name}`);
        cy.getByTestId(`toggle-${PURPOSE_5.name}`).should("not.exist");
        cy.get("#legal-basis-select").select("Legitimate interests");
        cy.getByTestId(`toggle-${PURPOSE_1.name}`).should("not.exist");
        cy.getByTestId(`toggle-${PURPOSE_5.name}`);

        // Vendors tab
        cy.get("#fides-tab-Vendors").click();
        cy.get("span").contains(VENDOR_1.name).click();
        cy.get(`div[id="${VENDOR_1.name}"]`).within(() => {
          cy.get("li").should("not.exist");
          cy.get("#legal-basis-select").select("Legitimate interests");
          cy.get("li").contains(SPECIAL_PURPOSE_1.name);
        });
      });

      it("can group toggle", () => {
        // Toggle the parent toggle off
        cy.getByTestId("toggle-Purposes").click();
        cy.getByTestId(`toggle-${PURPOSE_1.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
          cy.get("input").should("not.be.checked");
        });
        // Toggle a child back on
        cy.getByTestId(`toggle-${PURPOSE_1.name}`).click();
        cy.getByTestId("toggle-Purposes").within(() => {
          cy.get("input").should("not.be.checked");
        });
      });
    });

    describe("saving preferences", () => {
      it("can opt in to all", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_preferences).to.eql([
              { id: PURPOSE_5.id, preference: "opt_in" },
              { id: PURPOSE_1.id, preference: "opt_in" },
              { id: PURPOSE_3.id, preference: "opt_in" },
              { id: PURPOSE_4.id, preference: "opt_in" },
              { id: PURPOSE_2.id, preference: "opt_in" },
            ]);
            expect(body.special_purpose_preferences).to.eql([
              { id: SPECIAL_PURPOSE_1.id, preference: "opt_in" },
            ]);
            expect(body.feature_preferences).to.eql([
              { id: FEATURE_1.id, preference: "opt_in" },
              { id: FEATURE_2.id, preference: "opt_in" },
            ]);
            expect(body.vendor_preferences).to.eql([
              { id: VENDOR_2.id, preference: "opt_in" },
            ]);
            expect(body.system_preferences).to.eql([
              { id: VENDOR_1.id, preference: "opt_in" },
            ]);
          });
        });
        // Verify the cookie on save
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          [
            PURPOSE_1.id,
            PURPOSE_2.id,
            PURPOSE_3.id,
            PURPOSE_4.id,
            PURPOSE_5.id,
          ].forEach((pid) => {
            expect(cookieKeyConsent.tcf_consent.purpose_preferences)
              .property(`${pid}`)
              .is.eql(true);
          });
          expect(cookieKeyConsent.tcf_consent.special_purpose_preferences)
            .property(`${SPECIAL_PURPOSE_1.id}`)
            .is.eql(true);
          [FEATURE_1.id, FEATURE_2.id].forEach((fid) => {
            expect(cookieKeyConsent.tcf_consent.feature_preferences)
              .property(`${fid}`)
              .is.eql(true);
          });
          expect(cookieKeyConsent.tcf_consent.vendor_preferences)
            .property(`${VENDOR_2.id}`)
            .is.eql(true);
          expect(cookieKeyConsent.tcf_consent.system_preferences)
            .property(`${VENDOR_1.id}`)
            .is.eql(true);
        });
      });

      it("can opt out of all", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt out of all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_preferences).to.eql([
              { id: PURPOSE_5.id, preference: "opt_out" },
              { id: PURPOSE_1.id, preference: "opt_out" },
              { id: PURPOSE_3.id, preference: "opt_out" },
              { id: PURPOSE_4.id, preference: "opt_out" },
              { id: PURPOSE_2.id, preference: "opt_out" },
            ]);
            expect(body.special_purpose_preferences).to.eql([
              { id: SPECIAL_PURPOSE_1.id, preference: "opt_out" },
            ]);
            expect(body.feature_preferences).to.eql([
              { id: FEATURE_1.id, preference: "opt_out" },
              { id: FEATURE_2.id, preference: "opt_out" },
            ]);
            expect(body.vendor_preferences).to.eql([
              { id: VENDOR_2.id, preference: "opt_out" },
            ]);
            expect(body.system_preferences).to.eql([
              { id: VENDOR_1.id, preference: "opt_out" },
            ]);
          });
        });
        // Verify the cookie on save
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          [
            PURPOSE_1.id,
            PURPOSE_2.id,
            PURPOSE_3.id,
            PURPOSE_4.id,
            PURPOSE_5.id,
          ].forEach((pid) => {
            expect(cookieKeyConsent.tcf_consent.purpose_preferences)
              .property(`${pid}`)
              .is.eql(false);
          });
          expect(cookieKeyConsent.tcf_consent.special_purpose_preferences)
            .property(`${SPECIAL_PURPOSE_1.id}`)
            .is.eql(false);
          [FEATURE_1.id, FEATURE_2.id].forEach((fid) => {
            expect(cookieKeyConsent.tcf_consent.feature_preferences)
              .property(`${fid}`)
              .is.eql(false);
          });
          expect(cookieKeyConsent.tcf_consent.vendor_preferences)
            .property(`${VENDOR_2.id}`)
            .is.eql(false);
          expect(cookieKeyConsent.tcf_consent.system_preferences)
            .property(`${VENDOR_1.id}`)
            .is.eql(false);
        });
      });

      it("can opt in to some and opt out of others", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.getByTestId(`toggle-${PURPOSE_1.name}`).click();
          cy.getByTestId(`toggle-${SPECIAL_PURPOSE_1.name}`).click();

          cy.get("#fides-tab-Features").click();
          cy.getByTestId(`toggle-${FEATURE_1.name}`).click();

          cy.get("#fides-tab-Vendors").click();
          cy.getByTestId(`toggle-${VENDOR_1.name}`).click();
          cy.get("button").contains("Save").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_preferences).to.eql([
              { id: PURPOSE_5.id, preference: "opt_in" },
              { id: PURPOSE_1.id, preference: "opt_out" },
              { id: PURPOSE_3.id, preference: "opt_in" },
              { id: PURPOSE_4.id, preference: "opt_in" },
              { id: PURPOSE_2.id, preference: "opt_in" },
            ]);
            expect(body.special_purpose_preferences).to.eql([
              { id: SPECIAL_PURPOSE_1.id, preference: "opt_out" },
            ]);
            expect(body.feature_preferences).to.eql([
              { id: FEATURE_1.id, preference: "opt_in" },
              { id: FEATURE_2.id, preference: "opt_out" },
            ]);
            expect(body.vendor_preferences).to.eql([
              { id: VENDOR_2.id, preference: "opt_in" },
            ]);
            expect(body.system_preferences).to.eql([
              { id: VENDOR_1.id, preference: "opt_out" },
            ]);
          });
        });
        // Verify the cookie on save
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          [PURPOSE_2.id, PURPOSE_3.id, PURPOSE_4.id, PURPOSE_5.id].forEach(
            (pid) => {
              expect(cookieKeyConsent.tcf_consent.purpose_preferences)
                .property(`${pid}`)
                .is.eql(true);
            }
          );
          expect(cookieKeyConsent.tcf_consent.purpose_preferences)
            .property(`${PURPOSE_1.id}`)
            .is.eql(false);
          expect(cookieKeyConsent.tcf_consent.special_purpose_preferences)
            .property(`${SPECIAL_PURPOSE_1.id}`)
            .is.eql(false);
          expect(cookieKeyConsent.tcf_consent.feature_preferences)
            .property(`${FEATURE_1.id}`)
            .is.eql(true);
          expect(cookieKeyConsent.tcf_consent.feature_preferences)
            .property(`${FEATURE_2.id}`)
            .is.eql(false);
          expect(cookieKeyConsent.tcf_consent.vendor_preferences)
            .property(`${VENDOR_2.id}`)
            .is.eql(true);
          expect(cookieKeyConsent.tcf_consent.system_preferences)
            .property(`${VENDOR_1.id}`)
            .is.eql(false);
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
              [PURPOSE_1.id]: true,
              [PURPOSE_2.id]: true,
              [PURPOSE_3.id]: true,
              [PURPOSE_4.id]: true,
              1: false,
              2: false,
              3: false,
              5: false,
              8: false,
            });
            expect(tcData.purpose.legitimateInterests).to.eql({
              [PURPOSE_5.id]: true,
              1: false,
            });
            expect(tcData.vendor.consents).to.eql({
              1: false,
              [VENDOR_2.id]: true,
            });
            expect(tcData.vendor.legitimateInterests).to.eql({});
          });
      });

      it("can handle inappropriate legint purposes", () => {
        cy.fixture("consent/experience_tcf.json").then((payload) => {
          const experience: PrivacyExperience = payload.items[0];
          // Set purpose with id 4 to LegInt which is not allowed!
          experience.tcf_purposes![1].legal_bases = ["Legitimate interests"];
          // Set the corresponding embedded vendor purpose too
          experience.tcf_vendors![0].purposes![0].legal_bases = [
            "Legitimate interests",
          ];
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
              4: false,
              [PURPOSE_2.id]: true,
              [PURPOSE_3.id]: true,
              [PURPOSE_4.id]: true,
              1: false,
              2: false,
              3: false,
              5: false,
              8: false,
            });
            expect(tcData.purpose.legitimateInterests).to.eql({
              // No id 4 here!
              [PURPOSE_5.id]: true,
              1: false,
            });
            expect(tcData.vendor.consents).to.eql({
              1: false,
              [VENDOR_2.id]: true,
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
          purpose_preferences: { [PURPOSE_1.id]: false, [PURPOSE_2.id]: true },
          special_purpose_preferences: { [SPECIAL_PURPOSE_1.id]: false },
          feature_preferences: { [FEATURE_1.id]: true, [FEATURE_2.id]: true },
          system_preferences: { [VENDOR_1.id]: false },
          vendor_preferences: { [VENDOR_2.id]: false },
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
      // Open the modal and move to the second layer
      cy.get("#fides-modal-link").click();
      cy.getByTestId("fides-modal-content").within(() => {
        cy.get("#fides-banner-button-secondary")
          .contains("Manage preferences")
          .click();
      });

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${SPECIAL_PURPOSE_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      // also verify that a purpose that was not part of the cookie is also opted out
      // (since it should have no current_preference, and default behavior is opt out)
      cy.getByTestId(`toggle-${PURPOSE_3.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-Features").click();
      cy.getByTestId(`toggle-${FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${FEATURE_2.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      cy.get("#fides-tab-Vendors").click();
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${VENDOR_1.name}`).within(() => {
        cy.get("input").should("not.be.checked");
      });
    });
  });
});
