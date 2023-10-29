/* eslint-disable no-underscore-dangle */
import {
  CONSENT_COOKIE_NAME,
  FidesCookie,
  FidesEndpointPaths,
  PrivacyExperience,
  UserConsentPreference,
} from "fides-js";
import { CookieKeyConsent } from "fides-js/src/lib/cookie";
import { API_URL } from "../support/constants";
import { OVERRIDE, stubConfig } from "../support/stubs";

const PURPOSE_2 = {
  id: 2,
  name: "Use limited data to select advertising",
  served_notice_history_id: "ser_4120a09f-f6df-4fa4-9563-dd976599f4f3",
};
const PURPOSE_4 = {
  id: 4,
  name: "Use profiles to select personalised advertising",
  served_notice_history_id: "ser_17af7d7a-078a-4522-ae66-ec8006f35587",
};
const PURPOSE_6 = {
  id: 6,
  name: "Use profiles to select personalised content",
  served_notice_history_id: "ser_07301c42-34bd-4b03-bdca-69dfe1936341",
};
const PURPOSE_7 = {
  id: 7,
  name: "Measure advertising performance",
  served_notice_history_id: "ser_7c525f99-6b2b-4ced-b2a0-220a04cb57e9",
};
const PURPOSE_9 = {
  id: 9,
  name: "Understand audiences through statistics or combinations of data from different sources",
  served_notice_history_id: "ser_4120a09f-f6df-4fa4-9563-dd976599f4f3",
};
const SPECIAL_PURPOSE_1 = {
  id: 1,
  name: "Ensure security, prevent and detect fraud, and fix errors",
};
const SYSTEM_1 = {
  id: "ctl_b3dde2d5-e535-4d9a-bf6e-a3b6beb01761",
  name: "Fides System",
  served_notice_history_id: "ser_5b1bc497-b4ba-489d-b39c-9ff352d460b0",
};
const VENDOR_1 = {
  id: "2",
  name: "Captify",
  served_notice_history_id: "ser_9f3641ce-9863-4a32-b4db-ef1aac9046db",
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
  served_notice_history_id: "ser_9f3641ce-9863-4a32-b4db-ef1aac9046db",
};

describe("Fides-js TCF", () => {
  describe("banner appears when it should", () => {
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
      cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
        fixture: "consent/notices_served_tcf.json",
      }).as("patchNoticesServed");
    });
  });

  describe("banner appears when it should", () => {
    beforeEach(() => {
      cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
        fixture: "consent/notices_served_tcf.json",
      }).as("patchNoticesServed");
    });
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
      cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
        fixture: "consent/notices_served_tcf.json",
      }).as("patchNoticesServed");
    });
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
      cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
        fixture: "consent/notices_served_tcf.json",
      }).as("patchNoticesServed");
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
          experience.tcf_vendor_relationships.push(newVendor);
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
        cy.get("@FidesUpdated").should("have.been.calledOnce");
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
        cy.get("#fides-tab-Vendors").click();
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
              "https://www.example.com/legitimate_interest_disclosure"
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
            'Captify stores cookies with a maximum duration of about 5 Day(s). These cookies may be refreshed. This vendor also uses other methods like "local storage" to store and access information on your device.'
          );
        });
        // Check the cookie disclosure on the system
        // First close the vendor
        cy.get(".fides-notice-toggle-title").contains(VENDOR_1.name).click();
        // Then open the system
        cy.get(".fides-notice-toggle-title").contains(SYSTEM_1.name).click();
        cy.get(".fides-disclosure-visible").within(() => {
          cy.get("p").contains(
            "Fides System stores cookies with a maximum duration of about 5 Day(s)"
          );
        });
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
      const expectedEndOfFidesString = ".IABE,1~";
      it("can opt in to all", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            cy.get("@FidesUIChanged").should("not.have.been.called");
            const { body } = interception.request;
            expect(body.purpose_consent_preferences).to.eql([
              {
                id: PURPOSE_4.id,
                preference: "opt_in",
                served_notice_history_id: PURPOSE_4.served_notice_history_id,
              },
              {
                id: PURPOSE_6.id,
                preference: "opt_in",
                served_notice_history_id: PURPOSE_6.served_notice_history_id,
              },
              {
                id: PURPOSE_7.id,
                preference: "opt_in",
                served_notice_history_id: PURPOSE_7.served_notice_history_id,
              },
              {
                id: PURPOSE_9.id,
                preference: "opt_in",
                served_notice_history_id: PURPOSE_9.served_notice_history_id,
              },
            ]);
            expect(body.purpose_legitimate_interests_preferences).to.eql([
              {
                id: PURPOSE_2.id,
                preference: "opt_in",
                served_notice_history_id: PURPOSE_2.served_notice_history_id,
              },
            ]);
            expect(body.special_purpose_preferences).to.eql(undefined);
            expect(body.feature_preferences).to.eql(undefined);
            expect(body.special_feature_preferences).to.eql([
              {
                id: SPECIAL_FEATURE_1.id,
                preference: "opt_in",
                served_notice_history_id:
                  SPECIAL_FEATURE_1.served_notice_history_id,
              },
            ]);
            expect(body.vendor_consent_preferences).to.eql([
              {
                id: VENDOR_1.id,
                preference: "opt_in",
                served_notice_history_id: VENDOR_1.served_notice_history_id,
              },
            ]);
            expect(body.vendor_legitimate_interests_preferences).to.eql([]);
            expect(body.system_legitimate_interests_preferences).to.eql([
              {
                id: SYSTEM_1.id,
                preference: "opt_in",
                served_notice_history_id: SYSTEM_1.served_notice_history_id,
              },
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
            cookieKeyConsent.fides_string?.endsWith(expectedEndOfFidesString)
          ).to.eql(true);
        });
      });

      it("can opt out of all", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt out of all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            cy.get("@FidesUIChanged").should("not.have.been.called");
            const { body } = interception.request;
            expect(body.purpose_consent_preferences).to.eql([
              {
                id: PURPOSE_4.id,
                preference: "opt_out",
                served_notice_history_id: PURPOSE_4.served_notice_history_id,
              },
              {
                id: PURPOSE_6.id,
                preference: "opt_out",
                served_notice_history_id: PURPOSE_6.served_notice_history_id,
              },
              {
                id: PURPOSE_7.id,
                preference: "opt_out",
                served_notice_history_id: PURPOSE_7.served_notice_history_id,
              },
              {
                id: PURPOSE_9.id,
                preference: "opt_out",
                served_notice_history_id: PURPOSE_9.served_notice_history_id,
              },
            ]);
            expect(body.purpose_legitimate_interests_preferences).to.eql([
              {
                id: PURPOSE_2.id,
                preference: "opt_out",
                served_notice_history_id: PURPOSE_2.served_notice_history_id,
              },
            ]);
            expect(body.special_purpose_preferences).to.eql(undefined);
            expect(body.feature_preferences).to.eql(undefined);
            expect(body.special_feature_preferences).to.eql([
              {
                id: SPECIAL_FEATURE_1.id,
                preference: "opt_out",
                served_notice_history_id:
                  SPECIAL_FEATURE_1.served_notice_history_id,
              },
            ]);
            expect(body.vendor_consent_preferences).to.eql([
              {
                id: VENDOR_1.id,
                preference: "opt_out",
                served_notice_history_id: VENDOR_1.served_notice_history_id,
              },
            ]);
            expect(body.vendor_legitimate_interests_preferences).to.eql([]);
            expect(body.system_legitimate_interests_preferences).to.eql([
              {
                id: SYSTEM_1.id,
                preference: "opt_out",
                served_notice_history_id: SYSTEM_1.served_notice_history_id,
              },
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
            cookieKeyConsent.fides_string?.endsWith(expectedEndOfFidesString)
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
          cy.get("@FidesUIChanged").its("callCount").should("equal", 3);
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(body.purpose_consent_preferences).to.eql([
              {
                id: PURPOSE_4.id,
                preference: "opt_out",
                served_notice_history_id: PURPOSE_4.served_notice_history_id,
              },
              {
                id: PURPOSE_6.id,
                preference: "opt_in",
                served_notice_history_id: PURPOSE_6.served_notice_history_id,
              },
              {
                id: PURPOSE_7.id,
                preference: "opt_in",
                served_notice_history_id: PURPOSE_7.served_notice_history_id,
              },
              {
                id: PURPOSE_9.id,
                preference: "opt_in",
                served_notice_history_id: PURPOSE_9.served_notice_history_id,
              },
            ]);
            expect(body.purpose_legitimate_interests_preferences).to.eql([
              {
                id: PURPOSE_2.id,
                preference: "opt_in",
                served_notice_history_id: PURPOSE_2.served_notice_history_id,
              },
            ]);
            expect(body.special_purpose_preferences).to.eql(undefined);
            expect(body.feature_preferences).to.eql(undefined);
            expect(body.special_feature_preferences).to.eql([
              {
                id: SPECIAL_FEATURE_1.id,
                preference: "opt_in",
                served_notice_history_id:
                  SPECIAL_FEATURE_1.served_notice_history_id,
              },
            ]);
            expect(body.vendor_consent_preferences).to.eql([
              {
                id: VENDOR_1.id,
                preference: "opt_out",
                served_notice_history_id: VENDOR_1.served_notice_history_id,
              },
            ]);
            expect(body.vendor_legitimate_interests_preferences).to.eql([]);
            expect(body.system_legitimate_interests_preferences).to.eql([
              {
                id: SYSTEM_1.id,
                preference: "opt_out",
                served_notice_history_id: SYSTEM_1.served_notice_history_id,
              },
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
            cookieKeyConsent.fides_string?.endsWith(expectedEndOfFidesString)
          ).to.eql(true);
        });
      });

      it("calls custom save preferences API fn instead of internal Fides API when it is provided in Fides.init", () => {
        const apiOptions = {
          /* eslint-disable @typescript-eslint/no-unused-vars */
          savePreferencesFn: (
            consent: CookieKeyConsent,
            fides_string: string | undefined,
            experience: PrivacyExperience
          ): Promise<void> => new Promise(() => {}),
          /* eslint-enable @typescript-eslint/no-unused-vars */
        };
        const spyObject = cy
          .spy(apiOptions, "savePreferencesFn")
          .as("mockSavePreferencesFn");
        cy.fixture("consent/experience_tcf.json").then((privacyExperience) => {
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
              apiOptions,
            },
            experience: privacyExperience.items[0],
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.get("#fides-modal-link").click();
            cy.getByTestId("consent-modal").within(() => {
              cy.get("button").contains("Opt out of all").click();
              cy.get("@FidesUpdated").then(() => {
                // eslint-disable-next-line @typescript-eslint/no-unused-expressions
                expect(spyObject).to.be.called;
                const spy = spyObject.getCalls();
                const { args } = spy[0];
                expect(args[0]).to.deep.equal({
                  data_sales: true,
                  tracking: false,
                });
                // the TC str is dynamically updated upon save preferences with diff timestamp, so we do a fuzzy match
                expect(args[1]).to.contain(".IABE,1~");
                expect(args[2]).to.deep.equal(privacyExperience.items[0]);
              });
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
        cy.fixture("consent/experience_tcf.json").then((experience) => {
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
              fidesDisableSaveApi: true,
            },
            experience: experience.items[0],
          });
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
              cookieKeyConsent.tcf_consent
                .vendor_legitimate_interests_preferences
            ).to.eql({});
            expect(
              cookieKeyConsent.tcf_consent.system_consent_preferences
            ).to.eql({});
            expect(
              cookieKeyConsent.tcf_consent
                .system_legitimate_interests_preferences
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
        cy.fixture("consent/experience_tcf.json").then((experience) => {
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience: experience.items[0],
          });
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

      it("skips saving preferences to API when disable save is set via query param", () => {
        cy.getCookie("fides_string").should("not.exist");
        cy.fixture("consent/experience_tcf.json").then((experience) => {
          stubConfig(
            {
              options: {
                isOverlayEnabled: true,
                tcfEnabled: true,
              },
              experience: experience.items[0],
            },
            null,
            null,
            { fides_disable_save_api: true }
          );
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
        cy.fixture("consent/experience_tcf.json").then((experience) => {
          stubConfig(
            {
              options: {
                isOverlayEnabled: true,
                tcfEnabled: true,
              },
              experience: experience.items[0],
            },
            null,
            null,
            null,
            { fides_disable_save_api: true }
          );
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
  });

  describe("second layer embedded", () => {
    it("automatically renders the second layer and can render tabs", () => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesEmbed: true,
          },
          experience: experience.items[0],
        });
      });
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
    it("can opt in to some and opt out of others", () => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesEmbed: true,
          },
          experience: experience.items[0],
        });
      });
      cy.getByTestId("consent-content").within(() => {
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
      // embed modal should not close on preferences save
      cy.getByTestId("consent-content").should("exist");
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
          cookieKeyConsent.tcf_consent.purpose_legitimate_interests_preferences
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
        expect(cookieKeyConsent.tcf_consent.system_consent_preferences).to.eql(
          {}
        );
      });
    });
    it("automatically renders the second layer when fidesEmbed is set via cookie", () => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.getCookie("fides_embed").should("not.exist");
      cy.setCookie("fides_embed", "true");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
          },
          experience: experience.items[0],
        });
      });
      // spot check a couple UI elements
      cy.get("#fides-tab-Purposes");
      // Purposes
      cy.getByTestId("toggle-Purposes").within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      cy.get("#fides-tab-Vendors").click();
      cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
    });
    it("automatically renders the second layer when fidesEmbed is set via query param", () => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience: experience.items[0],
          },
          null,
          null,
          { fides_embed: true }
        );
      });
      // spot check a couple UI elements
      cy.get("#fides-tab-Purposes");
      // Purposes
      cy.getByTestId("toggle-Purposes").within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      cy.get("#fides-tab-Vendors").click();
      cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
    });
    it("automatically renders the second layer when fidesEmbed is set via window obj", () => {
      cy.getCookie("fides_string").should("not.exist");
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience: experience.items[0],
          },
          null,
          null,
          null,
          { fides_embed: true }
        );
      });
      // spot check a couple UI elements
      cy.get("#fides-tab-Purposes");
      // Purposes
      cy.getByTestId("toggle-Purposes").within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      cy.get("#fides-tab-Vendors").click();
      cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
    });
  });

  describe("CMP API", () => {
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
        cy.get("@FidesUpdated").should("not.have.been.called");
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        // On slow connections, we should explicitly wait for FidesUpdated
        cy.get("@FidesUpdated").should("have.been.calledOnce");
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
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
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
          experience.tcf_vendor_relationships?.push({ ...vendor, id: "test" });

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
        cy.get("@FidesUpdated").should("have.been.calledTwice");
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

  /**
   * There are the following potential sources of user preferences:
   * 1) fides_string override option (via config.options.fidesString)
   * 2) DEFER: preferences API (via a custom function)
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
      const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
      const CREATED_DATE = "2022-12-24T12:00:00.000Z";
      const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
      const cookie: FidesCookie = {
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
        fides_string: "CPziCYAPziCYAGXABBENATEIAACAAAAAAAAAABEAAAAA.IABE",
      };
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
    };

    /**
     * TEST CASE #1:
     * ❌ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) DEFER: preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ✅ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from local cookie
     */
    it("prefers preferences from a cookie when both cookie and experience exist", () => {
      setFidesCookie();
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesString: undefined,
          },
          experience: experience.items[0],
        });
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
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
          expect(tcData.purpose.legitimateInterests).to.eql({
            [PURPOSE_2.id]: true,
            1: false,
          });
          expect(tcData.vendor.consents).to.eql({
            1: false,
            [VENDOR_1.id]: true,
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
     * ❌ 2) DEFER: preferences API (via a custom function)
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
        OVERRIDE.EMPTY
      );
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    /**
     * TEST CASE #3:
     * ❌ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) DEFER: preferences API (via a custom function)
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
        OVERRIDE.EMPTY
      );
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    /**
     * TEST CASE #4:
     * ✅ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) DEFER: preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ✅ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from fides_string option
     */
    it("prefers preferences from fides_string option when fides_string, experience, and cookie exist", () => {
      setFidesCookie();
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA.IABE,1~";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesString: fidesStringOverride,
          },
          experience: experience.items[0],
        });
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      // Open the modal
      cy.get("#fides-modal-link").click();

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use the default preference set in the experience which is true
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
        // this purpose was previously set to true from the experience, but it is overridden by the fides_string
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_6.name}-consent`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_7.name}-consent`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}-consent`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use the default preference set in the experience which is false
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-Features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      // this purpose is set to true in the experience, but since it was not defined in the fides_string,
      // it should use the default preference set in the experience which is true
      cy.get("#fides-tab-Vendors").click();
      cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${VENDOR_1.name}-consent`).within(() => {
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
     * TEST CASE #5:
     * ✅ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) DEFER: preferences API (via a custom function)
     * ❌ 3) local cookie (via fides_consent cookie)
     * ✅ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from fides_string option
     */
    it("prefers preferences from fides_string option when both fides_string and experience is provided and cookie does not exist", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA.IABE,1~";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesString: fidesStringOverride,
          },
          experience: experience.items[0],
        });
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      // Open the modal
      cy.get("#fides-modal-link").click();

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use the default preference set in the experience which is true
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
        // this purpose was previously set to true from the experience, but it is overridden by the fides_string
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_6.name}-consent`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_7.name}-consent`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}-consent`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use the default preference set in the experience which is false
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-Features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      // this purpose is set to true in the experience, but since it was not defined in the fides_string,
      // it should use the default preference set in the experience which is true
      cy.get("#fides-tab-Vendors").click();
      cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${VENDOR_1.name}-consent`).within(() => {
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
     * TEST CASE #6:
     * ✅ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) DEFER: preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ❌ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: ignore all preferences, do not load TCF experience
     */
    it("does nothing when fides_string option when both fides_string option and cookie exist but no experience exists (neither prefetch nor API)", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA.IABE,1~";
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
        OVERRIDE.EMPTY // return no experience
      );
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    /**
     * TEST CASE #7:
     * ✅ 1) fides_string override option (via config.options.fidesString)
     * ❌ 2) DEFER: preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ✅ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from fides_string option
     */
    it("prefers preferences from fides_string option when both fides_string option and cookie exist and experience is fetched from API", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA.IABE,1~";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      setFidesCookie();
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        cy.fixture("consent/geolocation_tcf.json").then((geo) => {
          stubConfig(
            {
              options: {
                isOverlayEnabled: true,
                tcfEnabled: true,
                fidesString: fidesStringOverride,
              },
              experience: OVERRIDE.UNDEFINED,
            },
            geo,
            experience
          );
        });
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.window().then((win) => {
          win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
        });
      });

      // Open the modal
      cy.get("#fides-modal-link").click();

      // Verify the toggles
      // Purposes
      cy.getByTestId(`toggle-${PURPOSE_2.name}`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use the default preference set in the experience which is true
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_4.name}-consent`).within(() => {
        // this purpose was previously set to true from the experience, but it is overridden by the fides_string
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_6.name}-consent`).within(() => {
        cy.get("input").should("not.be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_7.name}-consent`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${PURPOSE_9.name}-consent`).within(() => {
        // this purpose is set to true in the experience, but since it was not defined in the fides_string,
        // it should use the default preference set in the experience which is false
        cy.get("input").should("not.be.checked");
      });
      // Features
      cy.get("#fides-tab-Features").click();
      cy.getByTestId(`toggle-${SPECIAL_FEATURE_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      // Vendors
      // this purpose is set to true in the experience, but since it was not defined in the fides_string,
      // it should use the default preference set in the experience which is true
      cy.get("#fides-tab-Vendors").click();
      cy.getByTestId(`toggle-${SYSTEM_1.name}`).within(() => {
        cy.get("input").should("be.checked");
      });
      cy.getByTestId(`toggle-${VENDOR_1.name}-consent`).within(() => {
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
  });

  describe("fides_string override options", () => {
    it("uses fides_string when set via cookie", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA.IABE,1~";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      cy.getCookie("fides_string").should("not.exist");
      cy.setCookie("fides_string", fidesStringOverride);
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
          },
          experience: experience.items[0],
        });
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      // Open the modal
      cy.get("#fides-modal-link").click();

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
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA.IABE,1~";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      cy.getCookie("fides_string").should("not.exist");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience: experience.items[0],
          },
          null,
          null,
          { fides_string: fidesStringOverride }
        );
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      // Open the modal
      cy.get("#fides-modal-link").click();

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
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA.IABE,1~";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      cy.getCookie("fides_string").should("not.exist");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience: experience.items[0],
          },
          null,
          null,
          null,
          { fides_string: fidesStringOverride }
        );
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
      });
      // Open the modal
      cy.get("#fides-modal-link").click();

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
          const vendor = { ...baseVendor, id: `gacp.${id}`, name: `AC ${id}` };
          experience.tcf_vendor_consents.push({
            ...vendor,
            // Set some of these vendors without purpose_consents
            purpose_consents: idx % 2 === 0 ? [] : baseVendor.purpose_consents,
          });
          experience.tcf_vendor_relationships.push(vendor);
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
          ...AC_IDS.map((id) => ({ id: `gacp.${id}`, preference: "opt_in" })),
        ];
        expect(body.vendor_consent_preferences).to.eql(expected);

        // Check the cookie
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          const { fides_string: tcString } = cookieKeyConsent;
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
          ...AC_IDS.map((id) => ({ id: `gacp.${id}`, preference: "opt_out" })),
        ];
        expect(body.vendor_consent_preferences).to.eql(expected);

        // Check the cookie
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
          const cookieKeyConsent: FidesCookie = JSON.parse(
            decodeURIComponent(cookie!.value)
          );
          const { fides_string: tcString } = cookieKeyConsent;
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
      cy.get("@FidesUpdated").should("have.been.calledOnce");
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

    it("can initialize from an AC string", () => {
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
          purpose_consent_preferences: { 2: false, [PURPOSE_4.id]: true },
          special_feature_preferences: { [SPECIAL_FEATURE_1.id]: true },
          system_legitimate_interests_preferences: { [SYSTEM_1.id]: false },
          vendor_consent_preferences: { [VENDOR_1.id]: false },
        },
        tc_string: "CPzbcgAPzbcgAGXABBENATEIAACAAAAAAAAAABEAAAAA.IABE",
      };
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            // this TC string sets purpose 4 to false and purpose 7 to true
            // the appended AC string sets AC 42 to true
            fidesString:
              "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA.IABE,1~42.43.44",
          },
          experience: experience.items[0],
        });
      });

      cy.get("@FidesInitialized")
        .its("lastCall.args.0.detail.tcf_consent")
        .then((tcfConsent) => {
          // TC string setting worked
          expect(tcfConsent.purpose_consent_preferences).to.eql({
            1: false,
            2: false,
            3: false,
            4: false,
            5: false,
            6: false,
            7: true,
          });
          // AC string setting worked
          expect(tcfConsent.vendor_consent_preferences).to.eql({
            "gacp.42": true,
            "gacp.43": true,
            "gacp.44": true,
          });
        });
    });
  });
});
