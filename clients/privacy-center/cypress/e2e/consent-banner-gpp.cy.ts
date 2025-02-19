/**
 * The GPP extension is often cached by the Cypress browser. You may need to manually
 * clear your Cypress browser's cache in the Network tab if you are making changes to
 * the source file while also running tests.
 */

/* eslint-disable no-underscore-dangle */
import {
  ComponentType,
  CONSENT_COOKIE_NAME,
  FidesCookie,
  FidesEndpointPaths,
  PrivacyExperience,
} from "fides-js";

import { API_URL, TCF_VERSION_HASH } from "../support/constants";
import { mockCookie } from "../support/mocks";
import { stubConfig, stubTCFExperience } from "../support/stubs";

describe("Fides-js GPP extension", () => {
  /**
   * Visit the fides-js-components-demo page with optional overrides on experience
   */
  const visitDemoWithGPP = (
    props: {
      overrideExperience?: (experience: PrivacyExperience) => PrivacyExperience;
    },
    queryParams?: Cypress.VisitOptions["qs"],
  ) => {
    cy.fixture("consent/experience_gpp.json").then((payload) => {
      let experience = payload.items[0];
      if (props.overrideExperience) {
        experience = props.overrideExperience(payload.items[0]);
        cy.log(
          "Using overridden PrivacyExperience data from overrideExperience()",
          experience,
        );
      }
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
            tcfEnabled: false,
          },
          experience,
        },
        undefined,
        undefined,
        queryParams,
      );
    });
  };

  beforeEach(() => {
    cy.intercept("PATCH", `${API_URL}${FidesEndpointPaths.NOTICES_SERVED}`, {
      fixture: "consent/notices_served_tcf.json",
    }).as("patchNoticesServed");
  });

  it("does not load the GPP extension if it is not enabled", () => {
    cy.fixture("consent/experience_tcf.json").then((payload) => {
      const experience = payload.items[0];
      stubConfig({
        options: {
          isOverlayEnabled: true,
          tcfEnabled: true,
        },
        experience: { ...experience, gpp_settings: { enabled: false } },
      });
    });
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("@FidesUIShown").should("have.been.calledOnce");
      cy.get("div#fides-banner").should("be.visible");
      cy.window().then((win) => {
        expect(win.__gpp).to.eql(undefined);
      });
    });
  });

  describe("Fides is not initialized", () => {
    beforeEach(() => {
      visitDemoWithGPP({}, { init: false });
    });
    it("does not load the GPP extension", () => {
      cy.get("@FidesInitializing").should("not.have.been.called");
      cy.window().then((win) => {
        expect(win.__gpp).to.eql(undefined);
      });
    });
    it("can still load the GPP extension if initialized later", () => {
      cy.window().then((win) => {
        win.Fides.init(win.Fides.config);
        cy.waitUntilFidesInitialized().then(() => {
          expect(win.__gpp).to.not.eql(undefined);
        });
      });
    });
  });

  describe("with TCF and GPP enabled", () => {
    const tcfGppSettings = { enabled: true, enable_tcfeu_string: true };
    beforeEach(() => {
      stubTCFExperience({
        experienceFullOverride: { gpp_settings: tcfGppSettings },
        experienceMinimalOverride: { gpp_settings: tcfGppSettings },
      });
    });

    it("loads the gpp extension if it is enabled", () => {
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        cy.get("div#fides-banner").should("be.visible");
        cy.window().then((win) => {
          win.__gpp("ping", cy.stub().as("gppPing"));
          cy.get("@gppPing")
            .should("have.been.calledOnce")
            .its("lastCall.args")
            .then(([data, success]) => {
              expect(success).to.eql(true);
              expect(data.signalStatus).to.eql("not ready");
            });
        });
      });
    });

    /**
     * Follows the flow documented here for Event Order Example 1:
     * https://github.com/InteractiveAdvertisingBureau/Global-Privacy-Platform/blob/main/Core/CMP%20API%20Specification.md#eventlistener-
     * 1. initial data from stub
     * 2. listenerRegistered
     * 3. cmpStatus = loaded
     * 4. cmpDisplayStatus = visible
     * 5. User makes a choice
     * 6. cmpDisplayStatus = hidden
     * 7. sectionChange = tcfeuv2
     * 8. signalStatus = ready
     */
    it("fires appropriate gpp events for first time user", () => {
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        // TODO(PROD#1439): Because the stub is too late right now, we can't listen for events 3 and 4 yet.

        cy.window().then((win) => {
          win.__gpp("addEventListener", cy.stub().as("gppListener"));
        });

        cy.get("@gppListener")
          .should("have.been.calledOnce")
          .its("lastCall.args")
          .then(([data, success]) => {
            expect(success).to.eql(true);
            expect(data.eventName).to.eql("listenerRegistered");
            const { cmpDisplayStatus, signalStatus, gppString } = data.pingData;
            expect(cmpDisplayStatus).to.eql("visible");
            expect(signalStatus).to.eql("not ready");
            expect(gppString).to.eql("DBAA"); // empty string, header only
          });

        cy.get("button").contains("Opt in to all").click();
        cy.get("@FidesUpdated").should("have.been.calledOnce");

        const expected = [
          { eventName: "cmpDisplayStatus", data: "hidden" },
          { eventName: "sectionChange", data: "tcfeuv2" },
          { eventName: "signalStatus", data: "ready" },
        ];

        cy.get("@gppListener")
          .its("args")
          .then((args) => {
            expect(args.length).to.eql(4);
            // we already checked the first arg, so inspect the other three
            [args[1], args[2], args[3]].forEach(([data, success], idx) => {
              expect(success).to.eql(true);
              expect(data.eventName).to.eql(expected[idx].eventName);
              expect(data.data).to.eql(expected[idx].data);
            });
            // The gpp string should also have an extra section now and the header should
            // indicate TCF.
            // The use of a regex is necessary because part of the string is
            // date-based and changes each day. The first 6 characters are the
            // "Created" date, the next 6 are the "Last Updated" date.
            expect(args[3][0].pingData.gppString).to.match(
              /DBABMA~[a-zA-Z0-9]{6}[a-zA-Z0-9]{6}AGXABBENArEoABaAAEAAAAAAABEAAAAA/,
            );
            // the `PurposeConsents` should match the gpp string
            expect(
              args[3][0].pingData.parsedSections.tcfeuv2.PurposeConsents,
            ).to.eql([
              false,
              false,
              false,
              true,
              false,
              true,
              true,
              false,
              true,
              false,
              false,
              false,
              false,
              false,
              false,
              false,
              false,
              false,
              false,
              false,
              false,
              false,
              false,
              false,
            ]);
          });
      });
    });

    /**
     * Follows the flow documented here for Event Order Example 2:
     * https://github.com/InteractiveAdvertisingBureau/Global-Privacy-Platform/blob/main/Core/CMP%20API%20Specification.md#eventlistener-
     * 1. initial data from stub
     * 2. listenerRegistered
     * 3. cmpStatus = loaded
     * 4. signalStatus = ready
     * 5. User opens the consent layer to change their voice
     * 6. signalStatus = not ready
     * 7. cmpDisplayStatus = visible
     * 8. User makes their choice
     * 9. cmpDisplayStatus = hidden
     * 10. sectionChange = tcfeuv2
     * 11. signalStatus = ready
     */
    it("fires appropriate gpp events for returning user", () => {
      const tcString = "CPziCYAPziCYAGXABBENATEIAACAAAAAAAAAABEAAAAA";
      // Set a cookie to mimic a returning user
      const cookie = mockCookie({
        tcf_version_hash: TCF_VERSION_HASH,
        fides_string: tcString,
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      stubTCFExperience({
        experienceFullOverride: { gpp_settings: tcfGppSettings },
        experienceMinimalOverride: { gpp_settings: tcfGppSettings },
      });

      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("not.have.been.called");
        // TODO(PROD#1439): Because the stub is too late right now, we can't listen for events 3 and 4 yet.

        cy.window().then((win) => {
          win.__gpp("addEventListener", cy.stub().as("gppListener"));
        });

        // Check initial data which should signal Ready and have the cookie's TC string
        cy.get("@gppListener")
          .should("have.been.calledOnce")
          .its("lastCall.args")
          .then(([data, success]) => {
            expect(success).to.eql(true);
            expect(data.eventName).to.eql("listenerRegistered");
            const {
              cmpDisplayStatus,
              signalStatus,
              gppString,
              cmpStatus,
              applicableSections,
              supportedAPIs,
            } = data.pingData;
            expect(cmpStatus).to.eql("loaded");
            expect(cmpDisplayStatus).to.eql("hidden");
            expect(signalStatus).to.eql("ready");
            expect(applicableSections).to.eql([2]);
            expect(supportedAPIs).to.eql(["2:tcfeuv2"]);
            expect(gppString).to.contain(tcString);
          });

        // User opens the modal so signal should be "not ready" and display should be "visible"
        cy.get("#fides-modal-link").click();
        cy.get("@gppListener")
          .its("args")
          .then((args) => {
            expect(args.length).to.eql(3);
            // when modal opens, the signal status should be changed back to "not ready"
            const expected = [
              { eventName: "signalStatus", data: "not ready" },
              { eventName: "cmpDisplayStatus", data: "visible" },
            ];
            [args[1], args[2]].forEach(([data, success], idx) => {
              expect(success).to.eql(true);
              expect(data.eventName).to.eql(expected[idx].eventName);
              expect(data.data).to.eql(expected[idx].data);
            });
          });

        // User makes a choice
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt out of all").click();
          cy.get("@FidesUpdated").should("have.been.calledOnce");
        });
        cy.get("@gppListener")
          .its("args")
          .then((args) => {
            expect(args.length).to.eql(6);
            const expected = [
              { eventName: "cmpDisplayStatus", data: "hidden" },
              { eventName: "sectionChange", data: "tcfeuv2" },
              { eventName: "signalStatus", data: "ready" },
            ];
            [args[3], args[4], args[5]].forEach(([data, success], idx) => {
              expect(success).to.eql(true);
              expect(data.eventName).to.eql(expected[idx].eventName);
              expect(data.data).to.eql(expected[idx].data);
            });
            // Check that the TC string changed-still the same header, but different contents
            const { gppString } = args[5][0].pingData;
            expect(gppString).to.contain("DBABMA~");
            expect(gppString).not.to.contain(tcString);
          });
      });
    });

    /**
     * Expected flow for a returning user who opens but then closes the modal without making a change:
     * 1. listenerRegistered
     * 2. User opens the modal
     * 3. signalStatus = ready
     * 4. cmpDisplayStatus = visible
     * 5. User closes the modal which automatically triggers preference save
     * 6. cmpDisplayStatus = hidden
     * 7. signalStatus = not ready
     */
    it("can handle returning user closing the modal", () => {
      const tcString = "CPziCYAPziCYAGXABBENATEIAACAAAAAAAAAABEAAAAA";
      const cookie = mockCookie({
        tcf_version_hash: TCF_VERSION_HASH,
        fides_string: tcString,
      });
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      stubTCFExperience({
        experienceFullOverride: { gpp_settings: tcfGppSettings },
        experienceMinimalOverride: { gpp_settings: tcfGppSettings },
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.window().then((win) => {
          win.__gpp("addEventListener", cy.stub().as("gppListener"));
        });
        cy.get("#fides-modal-link").click();
        cy.get(".fides-modal-content .fides-close-button").click();

        // when modal opens, the signal status should be changed back to "not ready"
        const expected = [
          { eventName: "listenerRegistered", data: true },
          { eventName: "signalStatus", data: "not ready" },
          { eventName: "cmpDisplayStatus", data: "visible" },
          { eventName: "cmpDisplayStatus", data: "hidden" },
          { eventName: "signalStatus", data: "ready" },
          { eventName: "cmpDisplayStatus", data: "hidden" },
          { eventName: "sectionChange", data: "tcfeuv2" },
          { eventName: "signalStatus", data: "ready" },
        ];
        cy.get("@gppListener")
          .its("args")
          .then(
            (
              args: [{ eventName: string; data: string | boolean }, boolean][],
            ) => {
              args.forEach(([data, success], idx) => {
                expect(success).to.eql(true);
                expect(data.eventName).to.eql(expected[idx].eventName);
                expect(data.data).to.eql(expected[idx].data);
              });
            },
          );
      });
    });

    it("can handle TCF enabled globally but disabled in GPP", () => {
      stubTCFExperience({
        experienceFullOverride: {
          gpp_settings: { enabled: true, enable_tcfeu_string: false },
        },
        experienceMinimalOverride: {
          gpp_settings: { enabled: true, enable_tcfeu_string: false },
        },
      });

      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesInitialized").should("have.been.calledOnce");

        cy.window().then((win) => {
          win.__gpp("addEventListener", cy.stub().as("gppListener"));
        });
        cy.get("@FidesUIShown").should("have.been.calledOnce");
        cy.get("@gppListener")
          .its("lastCall.args")
          .then(([data, success]) => {
            expect(success).to.eql(true);
            expect(data.eventName).to.eql("cmpDisplayStatus");
            expect(data.data).to.eql("visible");
            const { signalStatus, gppString, supportedAPIs } = data.pingData;
            // when modal opens, the signal status should be changed back to "not ready"
            expect(signalStatus).to.eql("not ready");
            expect(supportedAPIs).to.eql([]);
            expect(gppString).to.eql("DBAA");
          });
      });
    });
  });

  describe("with TCF disabled and GPP enabled", () => {
    describe("when visiting from a state with an applicable section", () => {
      beforeEach(() => {
        visitDemoWithGPP({});
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("@FidesUIShown").should("have.been.calledOnce");
          cy.window().then((win) => {
            win.__gpp("addEventListener", cy.stub().as("gppListener"));
          });
        });
      });
      it("loads the gpp extension if it is enabled", () => {
        cy.window().then((win) => {
          win.__gpp("ping", cy.stub().as("gppPing"));
          cy.get("@gppPing")
            .should("have.been.calledOnce")
            .its("lastCall.args")
            .then(([data, success]) => {
              expect(success).to.eql(true);
              // because TCF is disabled, status can always be "ready"
              expect(data.signalStatus).to.eql("ready");
            });
        });
      });

      it("can go through the flow of user opting in to data sales and sharing", () => {
        cy.get("button").contains("Opt in to all").click();
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const fidesCookie: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            const { consent } = fidesCookie;
            expect(consent).to.eql({ data_sales_sharing_gpp_us_state: true });
          });
        });

        const expected = [
          // First two gppStrings indicate the data_sales_sharing_gpp_us_state notice was served and opted in (default)
          {
            eventName: "listenerRegistered",
            data: true,
            gppString: "DBABBg~BUoAAABY.QA",
          },
          {
            eventName: "cmpDisplayStatus",
            data: "hidden",
            gppString: "DBABBg~BUoAAABY.QA",
          },
          // Second two gppStrings indicate the data_sales_sharing_gpp_us_state notice was served and opted into
          {
            eventName: "sectionChange",
            data: "usca",
            gppString: "DBABBg~BUoAAABY.QA",
          },
          {
            eventName: "signalStatus",
            data: "ready",
            gppString: "DBABBg~BUoAAABY.QA",
          },
        ];
        // Check the GPP events
        cy.get("@gppListener")
          .its("args")
          .then(
            (
              args: [
                { eventName: string; data: string | boolean; pingData: any },
                boolean,
              ][],
            ) => {
              args.forEach(([data, success], idx) => {
                expect(success).to.eql(true);
                expect(data.eventName).to.eql(expected[idx].eventName);
                expect(data.data).to.eql(expected[idx].data);
                expect(data.pingData.gppString).to.eql(expected[idx].gppString);
              });
            },
          );
        cy.get("@gppListener")
          .its("lastCall.args")
          .then((args) => {
            const [data] = args;
            expect(data.pingData.applicableSections).to.eql([8]);
            // TODO: (HJ-196) as locations and regulations are set, this value may change as it is currently hard coded
            expect(data.pingData.supportedAPIs).to.eql([
              "8:usca",
              "10:usco",
              "12:usct",
              "11:usut",
              "9:usva",
              "17:usde",
              "13:usfl",
              "18:usia",
              "14:usmt",
              "19:usne",
              "20:usnh",
              "21:usnj",
              "22:ustn",
              "16:ustx",
            ]);
          });
      });

      it("can go through the flow of user opting out of data sales and sharing", () => {
        cy.get("button").contains("Opt out of all").click();
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const fidesCookie: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            const { consent } = fidesCookie;
            expect(consent).to.eql({ data_sales_sharing_gpp_us_state: false });
          });
        });

        const expected = [
          // First two gppStrings indicate the data_sales_sharing_gpp_us_state notice was served and opted in (default)
          {
            eventName: "listenerRegistered",
            data: true,
            gppString: "DBABBg~BUoAAABY.QA",
          },
          {
            eventName: "cmpDisplayStatus",
            data: "hidden",
            gppString: "DBABBg~BUoAAABY.QA",
          },
          // Second two gppStrings indicate the data_sales_sharing_gpp_us_state notice was served and opted out
          {
            eventName: "sectionChange",
            data: "usca",
            gppString: "DBABBg~BUUAAABY.QA",
          },
          {
            eventName: "signalStatus",
            data: "ready",
            gppString: "DBABBg~BUUAAABY.QA",
          },
        ];
        // Check the GPP events
        cy.get("@gppListener")
          .its("args")
          .then(
            (
              args: [
                { eventName: string; data: string | boolean; pingData: any },
                boolean,
              ][],
            ) => {
              args.forEach(([data, success], idx) => {
                expect(success).to.eql(true);
                expect(data.eventName).to.eql(expected[idx].eventName);
                expect(data.data).to.eql(expected[idx].data);
                expect(data.pingData.gppString).to.eql(expected[idx].gppString);
              });
            },
          );
      });

      it("can handle a returning user", () => {
        const cookie = mockCookie({
          consent: { data_sales_sharing_gpp_us_state: true },
        });
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
        visitDemoWithGPP({});
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("@FidesUIShown").should("not.have.been.called");

          cy.window().then((win) => {
            win.__gpp("addEventListener", cy.stub().as("gppListener"));
          });
          // Initializes string properly
          cy.get("@gppListener")
            .its("args")
            .then((args) => {
              const [data, success] = args[0];
              expect(success).to.eql(true);
              // Opt in string
              expect(data.pingData.applicableSections).to.eql([8]);
              expect(data.pingData.gppString).to.eql("DBABBg~BUoAAABY.QA");
              // because TCF is disabled, status can always be "ready"
              expect(data.pingData.signalStatus).to.eql("ready");
            });
        });
      });
    });
    describe("when visiting from a state that does not have an applicable section", () => {
      beforeEach(() => {
        visitDemoWithGPP({
          overrideExperience: (experience: any) => {
            /* eslint-disable no-param-reassign */
            experience.region = "us_nc";
            return experience;
          },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("@FidesUIShown").should("have.been.calledOnce");
          cy.window().then((win) => {
            win.__gpp("addEventListener", cy.stub().as("gppListener"));
          });
        });
      });

      it("loads the gpp extension if it is enabled", () => {
        cy.window().then((win) => {
          win.__gpp("ping", cy.stub().as("gppPing"));
          cy.get("@gppPing")
            .should("have.been.calledOnce")
            .its("lastCall.args")
            .then(([data, success]) => {
              expect(success).to.eql(true);
              // because TCF is disabled, status can always be "ready"
              expect(data.signalStatus).to.eql("ready");
              expect(data.applicableSections).to.eql([-1]);
            });
        });
      });

      it("can go through the flow of user opting in to data sales and sharing", () => {
        cy.get("button").contains("Opt in to all").click();

        // Check the GPP events
        cy.get("@gppListener")
          .its("args")
          .then((args) => {
            // this is the "signalStatus" of "ready" event
            const [data, success] = args[2];
            expect(success).to.eql(true);
            expect(data.pingData.applicableSections).to.eql([-1]);
            expect(data.pingData.signalStatus).to.eql("ready");
          });
      });

      it("can go through the flow of user opting out of data sales and sharing", () => {
        cy.get("button").contains("Opt out of all").click();

        // Check the GPP events
        cy.get("@gppListener")
          .its("args")
          .then((args) => {
            // this is the "signalStatus" of "ready" event
            const [data, success] = args[2];
            expect(success).to.eql(true);
            expect(data.pingData.applicableSections).to.eql([-1]);
            expect(data.pingData.signalStatus).to.eql("ready");
          });
      });

      it("can handle a returning user", () => {
        const cookie = mockCookie({
          consent: { data_sales_sharing_gpp_us_state: true },
        });
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
        visitDemoWithGPP({
          overrideExperience: (experience: any) => {
            /* eslint-disable no-param-reassign */
            experience.region = "us_nc";
            return experience;
          },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("@FidesUIShown").should("not.have.been.called");
          cy.window().then((win) => {
            win.__gpp("addEventListener", cy.stub().as("gppListener"));
          });
          // Initializes string properly
          cy.get("@gppListener")
            .its("args")
            .then((args) => {
              const [data, success] = args[0];
              expect(success).to.eql(true);
              // Opt in string
              expect(data.pingData.applicableSections).to.eql([-1]);
              expect(data.pingData.gppString).to.eql("DBAA");
              // because TCF is disabled, status can always be "ready"
              expect(data.pingData.signalStatus).to.eql("ready");
            });
        });
      });
    });
  });

  describe("with GPP enabled for a Headless experience", () => {
    describe("when visiting from a state with an applicable section", () => {
      beforeEach(() => {
        visitDemoWithGPP({
          overrideExperience: (experience: any) => {
            /* eslint-disable no-param-reassign */
            experience.experience_config.component === ComponentType.HEADLESS;
            return experience;
          },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("@FidesUIShown").should("have.been.calledOnce");
          cy.window().then((win) => {
            win.__gpp("addEventListener", cy.stub().as("gppListener"));
          });
        });
      });
      it("loads the gpp extension if it is enabled", () => {
        cy.window().then((win) => {
          win.__gpp("ping", cy.stub().as("gppPing"));
          cy.get("@gppPing")
            .should("have.been.calledOnce")
            .its("lastCall.args")
            .then(([data, success]) => {
              expect(success).to.eql(true);
              // because TCF is disabled, status can always be "ready"
              expect(data.signalStatus).to.eql("ready");
            });
        });
      });

      it("can handle a returning user", () => {
        const cookie = mockCookie({
          consent: { data_sales_sharing_gpp_us_state: true },
        });
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
        visitDemoWithGPP({
          overrideExperience: (experience: any) => {
            /* eslint-disable no-param-reassign */
            experience.experience_config.component === ComponentType.HEADLESS;
            return experience;
          },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.window().then((win) => {
            win.__gpp("addEventListener", cy.stub().as("gppListener"));
          });
          // Initializes string properly
          cy.get("@gppListener")
            .its("args")
            .then((args) => {
              const [data, success] = args[0];
              expect(success).to.eql(true);
              // Opt in string
              expect(data.pingData.applicableSections).to.eql([8]);
              expect(data.pingData.gppString).to.eql("DBABBg~BUoAAABY.QA");
              // because TCF is disabled, status can always be "ready"
              expect(data.pingData.signalStatus).to.eql("ready");
            });
        });
      });
    });
    describe("when visiting from a state that does not have an applicable section", () => {
      beforeEach(() => {
        visitDemoWithGPP({
          overrideExperience: (experience: any) => {
            /* eslint-disable no-param-reassign */
            experience.experience_config.component === ComponentType.HEADLESS;
            experience.region = "us_nc";
            return experience;
          },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.window().then((win) => {
            win.__gpp("addEventListener", cy.stub().as("gppListener"));
          });
        });
      });

      it("loads the gpp extension if it is enabled", () => {
        cy.window().then((win) => {
          win.__gpp("ping", cy.stub().as("gppPing"));
          cy.get("@gppPing")
            .should("have.been.calledOnce")
            .its("lastCall.args")
            .then(([data, success]) => {
              expect(success).to.eql(true);
              // because TCF is disabled, status can always be "ready"
              expect(data.signalStatus).to.eql("ready");
              expect(data.applicableSections).to.eql([-1]);
            });
        });
      });

      it("can handle a returning user", () => {
        const cookie = mockCookie({
          consent: { data_sales_sharing_gpp_us_state: true },
        });
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
        visitDemoWithGPP({
          overrideExperience: (experience: any) => {
            /* eslint-disable no-param-reassign */
            experience.experience_config.component === ComponentType.HEADLESS;
            experience.region = "us_nc";
            return experience;
          },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.window().then((win) => {
            win.__gpp("addEventListener", cy.stub().as("gppListener"));
          });
          // Initializes string properly
          cy.get("@gppListener")
            .its("args")
            .then((args) => {
              const [data, success] = args[0];
              expect(success).to.eql(true);
              // Opt in string
              expect(data.pingData.applicableSections).to.eql([-1]);
              expect(data.pingData.gppString).to.eql("DBAA");
              // because TCF is disabled, status can always be "ready"
              expect(data.pingData.signalStatus).to.eql("ready");
            });
        });
      });
    });
  });

  describe("with GPP forced", () => {
    it("loads the gpp extension", () => {
      cy.visit({
        url: "/fides-js-demo.html",
        qs: { gpp: "true" },
      });
      cy.window().then((win) => {
        win.__gpp("ping", cy.stub().as("gppPing"));
        cy.get("@gppPing")
          .should("have.been.calledOnce")
          .its("lastCall.args")
          .then(([, success]) => {
            expect(success).to.eql(true);
          });
      });
    });
  });
});
