/* eslint-disable no-underscore-dangle */
import {
  CONSENT_COOKIE_NAME,
  ConsentMethod,
  FidesCookie,
  FidesEndpointPaths,
  PrivacyExperience,
} from "fides-js";
import { TCString } from "@iabtechlabtcf/core";
import { NoticeConsent } from "fides-js/src/lib/consent-types";
import { FIDES_SEPARATOR } from "fides-js/src/lib/tcf/constants";
import {
  API_URL,
  TCF_VERSION_HASH,
  TEST_OVERRIDE_WINDOW_PATH,
} from "../support/constants";
import { mockCookie, mockTcfVendorObjects } from "../support/mocks";
import { OVERRIDE, stubConfig } from "../support/stubs";

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
  const model = TCString.decode(tcString!);
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
  const acString = fidesString?.split("1~")[1];
  expect(acString).to.be.a("string");
  const values = acString!
    .split(".")
    .map((id) => +id)
    .sort();
  expect(values).to.eql(ids.sort());
};

const fidesVendorIdToId = (fidesId: string) => +fidesId.split(".")[1];

describe("Fides-js TCF", () => {
  describe("banner appears when it should", () => {
    beforeEach(() => {
      cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
        fixture: "consent/notices_served_tcf.json",
      }).as("patchNoticesServed");
    });

    it("should render the banner if there is no saved version hash", () => {
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
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        cy.get("div#fides-banner").should("be.visible");
      });
    });

    it("should not render the banner if the saved hashes match", () => {
      const cookie = mockCookie({
        tcf_version_hash: TCF_VERSION_HASH,
      });
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
      cy.waitUntilFidesInitialized().then(() => {
        // The banner has a delay, so in order to assert its non-existence, we have
        // to give it a chance to come up first. Otherwise, the following gets will
        // pass regardless.
        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.get("@FidesUIShown").should("not.have.been.called");
        cy.get("div#fides-banner").should("not.exist");
      });
    });
    it("should not render the banner if fides_disable_banner is true", () => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesDisableBanner: true,
          },
          experience: experience.items[0],
        });
      });
      cy.waitUntilFidesInitialized().then(() => {
        // The banner has a delay, so in order to assert its non-existence, we have
        // to give it a chance to come up first. Otherwise, the following gets will
        // pass regardless.
        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.get("@FidesUIShown").should("not.have.been.called");
        cy.get("div#fides-banner").should("not.exist");
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
        [PURPOSE_4, PURPOSE_9, PURPOSE_7, PURPOSE_2].forEach((purpose) => {
          cy.get("li").contains(purpose.name);
        });
      });
    });

    it("can open the modal", () => {
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });
      cy.get("#fides-tab-purposes");
    });

    it("can open the modal from vendor information", () => {
      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Vendors").click();
      });
      cy.get("#fides-tab-vendors");
      cy.getByTestId(`toggle-${VENDOR_1.name}`);
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
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience,
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
            'Captify stores cookies with a maximum duration of about this many days: 5. These cookies may be refreshed. This vendor also uses other methods like "local storage" to store and access information on your device.'
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
            "Fides System stores cookies with a maximum duration of about this many days: 5."
          );
        });
      });

      it("can fire FidesUIChanged events", () => {
        cy.getByTestId(`toggle-${PURPOSE_4.name}`).click();
        cy.get("@FidesUIChanged").its("callCount").should("equal", 1);

        cy.getByTestId(`toggle-${PURPOSE_6.name}`).click();
        cy.get("@FidesUIChanged").its("callCount").should("equal", 2);
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
            JSON.stringify(experience.tcf_special_purposes[0])
          );
          const legintSpecialPurpose = {
            ...specialPurposeCopy,
            id: 2,
            name: legintSpecialPurposeName,
            legal_bases: ["Legitimate interests"],
          };
          experience.tcf_special_purposes.push(legintSpecialPurpose);
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience,
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
            cy.getByTestId(`toggle-${PURPOSE_2.name}`).should("not.exist");

            // Now check legint page
            cy.get("button").contains("Legitimate interest").click();
            consentPurposes.forEach((p) => {
              cy.getByTestId(`toggle-${p.name}`).should("not.exist");
            });
            cy.getByTestId(`toggle-${PURPOSE_2.name}`);
            cy.get("span").contains(legintSpecialPurposeName);
            cy.get("span").contains(SPECIAL_PURPOSE_1.name).should("not.exist");
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
          stubConfig({
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
            },
            experience: updatedExperience,
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
      const vendorsDisclosed = ".IABE";
      it("can opt in to all", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
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
            decodeURIComponent(cookie!.value)
          );
          expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
            ConsentMethod.ACCEPT
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
            ids: [],
          });
          expect(
            cookieKeyConsent.tcf_consent.system_consent_preferences
          ).to.eql({});
          expect(
            cookieKeyConsent.tcf_consent.system_legitimate_interests_preferences
          )
            .property(`${SYSTEM_1.id}`)
            .is.eql(true);

          // Confirm vendors_disclosed section does not exist
          expect(cookieKeyConsent.fides_string).to.not.contain(
            vendorsDisclosed
          );
        });
      });

      it("can opt out of all", () => {
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt out of all").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            cy.get("@FidesUIChanged").should("not.have.been.called");
            const { body } = interception.request;
            expect(interception.request.body.method).to.eql(
              ConsentMethod.REJECT
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
              decodeURIComponent(cookie!.value)
            );
            expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
              ConsentMethod.REJECT
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
              ids: [],
            });
            expect(
              cookieKeyConsent.tcf_consent.system_consent_preferences
            ).to.eql({});
            expect(
              cookieKeyConsent.tcf_consent
                .system_legitimate_interests_preferences
            )
              .property(`${SYSTEM_1.id}`)
              .is.eql(false);
            // Confirm vendors_disclosed section does not exist
            expect(cookieKeyConsent.fides_string).to.not.contain(
              vendorsDisclosed
            );
          });
        });
      });

      it("can opt in to some and opt out of others", () => {
        cy.getByTestId("consent-modal").within(() => {
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
          cy.get("@FidesUIChanged").its("callCount").should("equal", 3);
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            expect(interception.request.body.method).to.eql(ConsentMethod.SAVE);
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
            decodeURIComponent(cookie!.value)
          );
          expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
            ConsentMethod.SAVE
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
            ids: [],
          });
          expect(
            cookieKeyConsent.tcf_consent.system_legitimate_interests_preferences
          )
            .property(`${SYSTEM_1.id}`)
            .is.eql(false);
          expect(
            cookieKeyConsent.tcf_consent.system_consent_preferences
          ).to.eql({});
          // Confirm vendors_disclosed section does not exist
          expect(cookieKeyConsent.fides_string).to.not.contain(
            vendorsDisclosed
          );
        });
      });

      it("calls custom save preferences API fn instead of internal Fides API when it is provided in Fides.init", () => {
        const apiOptions = {
          /* eslint-disable @typescript-eslint/no-unused-vars */
          savePreferencesFn: async (
            consentMethod: ConsentMethod,
            consent: NoticeConsent,
            fides_string: string | undefined,
            experience: PrivacyExperience
          ): Promise<void> => {},
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
                  expect(args[2]).to.contain("AA,1~");
                  expect(args[3]).to.deep.equal(privacyExperience.items[0]);
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
            expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
              ConsentMethod.REJECT
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
              ids: [],
            });
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
      cy.get("#fides-tab-purposes");
      cy.get("@FidesUIShown").should("have.been.calledOnce");
      checkDefaultExperienceRender();
    });
    it("automatically renders the second layer even when fides_disable_banner is true", () => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesEmbed: true,
            fidesDisableBanner: true,
          },
          experience: experience.items[0],
        });
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        cy.get("div#fides-banner").should("not.exist");
        cy.get("div#fides-consent-content").should("exist");
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
          decodeURIComponent(cookie!.value)
        );
        expect(cookieKeyConsent.fides_meta.consentMethod).to.eql(
          ConsentMethod.SAVE
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
          ids: [],
        });
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
      checkDefaultExperienceRender();
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
      checkDefaultExperienceRender();
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
      checkDefaultExperienceRender();
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
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });
    });

    it("makes API available as soon as possible", () => {
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
        win.__tcfapi("addEventListener", 2, (tcData, success) => {
          expect(success).to.eql(true);
          expect(tcData.gdprApplies).to.eql(true);
        });
      });
    });

    it("gdpr applies can be overridden to false", () => {
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            fidesTcfGdprApplies: false,
          },
          experience: experience.items[0],
        });
      });
      cy.window().then((win) => {
        win.__tcfapi("addEventListener", 2, (tcData, success) => {
          expect(success).to.eql(true);
          expect(tcData.gdprApplies).to.eql(false);
        });
      });
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
            expect(tcData.vendor.legitimateInterests).to.eql({});
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
        OVERRIDE.EMPTY
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
        OVERRIDE.EMPTY
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
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
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
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
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
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
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
     * ❌ 2) preferences API (via a custom function)
     * ✅ 3) local cookie (via fides_consent cookie)
     * ❌ 4) "prefetched" experience (via config.options.experience)
     * ✅ 5) experience API (via GET /privacy-experience)
     *
     * EXPECTED RESULT: use preferences from fides_string option
     */
    it("prefers preferences from fides_string option when both fides_string option and cookie exist and experience is fetched from API", () => {
      const fidesStringOverride =
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
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
      const fidesStringOverride = "invalid-string,1~";
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
        "CP0gqMAP0gqMAGXABBENATEIABaAAEAAAAAAABEAAAAA,1~";
      const fidesString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      setFidesCookie();
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        cy.fixture("consent/geolocation_tcf.json").then((geo) => {
          const apiOptions = {
            getPreferencesFn: async () => ({ fides_string: fidesString }),
          };
          const spyObject = cy.spy(apiOptions, "getPreferencesFn");
          stubConfig(
            {
              options: {
                isOverlayEnabled: true,
                tcfEnabled: true,
                apiOptions,
                fidesString: fidesStringOverride,
              },
              experience: OVERRIDE.UNDEFINED,
            },
            geo,
            experience
          );
          cy.waitUntilFidesInitialized().then(() => {
            cy.window().then((win) => {
              win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
            });
            // eslint-disable-next-line @typescript-eslint/no-unused-expressions
            expect(spyObject).to.be.called;
          });
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
      const fidesString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
      const versionHash = "091834y";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"; // without disclosed vendors
      setFidesCookie();
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        cy.fixture("consent/geolocation_tcf.json").then((geo) => {
          const apiOptions = {
            getPreferencesFn: async () => ({
              fides_string: fidesString,
              version_hash: versionHash,
            }),
          };
          const spyObject = cy.spy(apiOptions, "getPreferencesFn");
          stubConfig(
            {
              options: {
                isOverlayEnabled: true,
                tcfEnabled: true,
                apiOptions,
              },
              experience: OVERRIDE.UNDEFINED,
            },
            geo,
            experience
          );
          cy.waitUntilFidesInitialized().then(() => {
            cy.window().then((win) => {
              win.__tcfapi("addEventListener", 2, cy.stub().as("TCFEvent"));
            });
            // eslint-disable-next-line @typescript-eslint/no-unused-expressions
            expect(spyObject).to.be.called;
            // confirm cookie reflects version_hash from custom preferences API
            cy.get("@FidesInitialized")
              .should("have.been.calledTwice")
              .its("firstCall.args.0.detail.tcf_version_hash")
              .should("deep.equal", versionHash);
          });
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
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        cy.fixture("consent/geolocation_tcf.json").then((geo) => {
          stubConfig(
            {
              options: {
                isOverlayEnabled: true,
                tcfEnabled: true,
                fidesString: undefined,
              },
              experience: OVERRIDE.UNDEFINED,
            },
            geo,
            experience
          );
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
        "CP0gqMAP0gqMAGXABBENATEIABaAAEAAAAAAABEAAAAA,1~";
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
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
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
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
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
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
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
        "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~";
      const expectedTCString = "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA";
      cy.getCookie("fides_string").should("not.exist");
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
              // this path is hard-coded in commands.ts for ease of testing
              customOptionsPath: TEST_OVERRIDE_WINDOW_PATH,
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
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
              customOptionsPath: "window.nonexistent_object",
            },
            experience: experience.items[0],
          },
          null,
          null,
          null,
          { fides_string: "foo" }
        );
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
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
              tcfEnabled: true,
              customOptionsPath: "window.nonexistent_object.nested.path",
            },
            experience: experience.items[0],
          },
          null,
          null,
          null,
          { fides_string: "foo" }
        );
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
      cy.get("div#fides-banner").within(() => {
        cy.get("#fides-button-group").within(() => {
          cy.get("button").contains("Manage preferences").click();
        });
      });
    });

    it("can opt in to AC vendors and generate string", () => {
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
              decodeURIComponent(cookie!.value)
            );
            const { fides_string: tcString } = cookieKeyConsent;
            const acString = tcString?.split(",")[1];
            expect(acString).to.eql(acceptAllAcString);
          });
        });
      });
    });

    it("can opt out of AC vendors and generate string", () => {
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
              decodeURIComponent(cookie!.value)
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

    it("can initialize from an AC string", () => {
      const cookie = mockCookie({
        fides_string: "CPzbcgAPzbcgAGXABBENATEIAACAAAAAAAAAABEAAAAA",
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      cy.fixture("consent/experience_tcf.json").then((experience) => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            tcfEnabled: true,
            // this TC string sets purpose 4 to false and purpose 7 to true
            // the appended AC string sets AC 42,43,44 to true
            fidesString:
              "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA,1~42.43.44",
          },
          experience: experience.items[0],
        });
      });

      cy.get("@FidesInitialized")
        .should("have.been.calledTwice")
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
                embedded
              );
            } else {
              experience.tcf_purpose_legitimate_interests[0].systems.push(
                embedded
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
});
