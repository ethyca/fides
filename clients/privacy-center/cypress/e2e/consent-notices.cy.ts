import {
  ConsentOptionCreate,
  PrivacyNoticeResponseWithUserPreferences,
} from "~/types/api";
import { CONSENT_COOKIE_NAME, FidesCookie } from "fides-js";
import { API_URL } from "../support/constants";

const VERIFICATION_CODE = "112358";
const PRIVACY_NOTICE_ID_1 = "pri_b4360591-3cc7-400d-a5ff-a9f095ab3061";
const PRIVACY_NOTICE_ID_2 = "pri_b558ab1f-5367-4f0d-94b1-ec06a81ae821";

describe("Privacy notice driven consent", () => {
  beforeEach(() => {
    // Seed local storage with verification data
    cy.window().then((win) => {
      win.localStorage.setItem(
        "consentRequestId",
        JSON.stringify("consent-request-id")
      );
      win.localStorage.setItem(
        "verificationCode",
        JSON.stringify(VERIFICATION_CODE)
      );
    });

    // Intercept sending identity data to the backend to access /consent page
    cy.intercept(
      "POST",
      `${API_URL}/consent-request/consent-request-id/verify`,
      { fixture: "consent/verify" }
    ).as("postConsentRequestVerify");

    // Experience intercept
    cy.intercept("GET", `${API_URL}/privacy-experience/*`, {
      fixture: "consent/experience.json",
    }).as("getExperience");

    // Patch privacy preference intercept
    cy.intercept(
      "PATCH",
      `${API_URL}/consent-request/consent-request-id/privacy-preferences*`,
      {
        fixture: "consent/privacy_preferences.json",
      }
    ).as("patchPrivacyPreference");
  });

  it("populates its header from the experience config", () => {
    cy.visit("/consent");
    cy.getByTestId("consent");
    cy.overrideSettings({
      IS_OVERLAY_DISABLED: false,
    });
    cy.wait("@getExperience");
    cy.getByTestId("consent-heading").contains("Privacy notice driven");
    cy.getByTestId("consent-description").contains(
      "Manage all of your notices here."
    );
  });

  it("renders from privacy notices when there is no initial data", () => {
    // Visit the consent page with notices enabled
    cy.visit("/consent");
    cy.getByTestId("consent");
    cy.overrideSettings({
      IS_OVERLAY_DISABLED: false,
    });
    cy.wait("@getExperience").then((interception) => {
      const { url } = interception.request;
      expect(url).contains("fides_user_device_id");
    });
    // Opt in, so should default to not checked
    cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
      cy.getRadio().should("not.be.checked");
    });
    // Opt out, so should default to checked
    cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_2}`).within(() => {
      cy.getRadio().should("be.checked");
    });

    // Opt in to the opt in notice
    cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
      cy.getRadio().should("not.be.checked").check({ force: true });
      cy.getRadio().should("be.checked");
    });

    cy.getByTestId("save-btn").click();
    cy.wait("@patchPrivacyPreference").then((interception) => {
      const { body } = interception.request;
      const { preferences, code, method } = body;
      expect(method).to.eql("button");
      expect(code).to.eql(VERIFICATION_CODE);
      expect(preferences.map((p: ConsentOptionCreate) => p.preference)).to.eql([
        "opt_in",
        "opt_in",
      ]);
      cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
          const cookie = JSON.parse(
            decodeURIComponent(cookieJson!.value)
          ) as FidesCookie;
          expect(body.browser_identity.fides_user_device_id).to.eql(
            cookie.identity.fides_user_device_id
          );
          const expectedConsent = { data_sales: true, advertising: true };
          const { consent } = cookie;
          expect(consent).to.eql(expectedConsent);
          cy.window().then((win) => {
            expect(win.Fides.consent).to.eql(expectedConsent);
          });
        });
      });
    });
  });

  it("renders from privacy notices when user has consented before", () => {
    cy.fixture("consent/experience.json").then((experience) => {
      const newExperience = { ...experience };
      const notices = newExperience.items[0].privacy_notices;
      newExperience.items[0].privacy_notices = notices.map(
        (notice: PrivacyNoticeResponseWithUserPreferences) => ({
          ...notice,
          ...{ current_preference: "opt_in" },
        })
      );
      cy.intercept("GET", `${API_URL}/privacy-experience/*`, {
        body: newExperience,
      }).as("getExperienceWithConsentHistory");
    });
    // Visit the consent page with notices enabled
    cy.visit("/consent");
    cy.getByTestId("consent");
    cy.overrideSettings({
      IS_OVERLAY_DISABLED: false,
    });
    // Both notices should be checked
    cy.wait("@getExperienceWithConsentHistory");
    cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
      cy.getRadio().should("be.checked");
    });
    cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_2}`).within(() => {
      cy.getRadio().should("be.checked");
    });

    cy.getByTestId("save-btn").click();
    cy.wait("@patchPrivacyPreference").then((interception) => {
      const { body } = interception.request;
      const { preferences } = body;
      expect(preferences.map((p: ConsentOptionCreate) => p.preference)).to.eql([
        "opt_in",
        "opt_in",
      ]);
    });
  });

  it("uses the device id found in an already existing cookie", () => {
    const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
    const now = "2023-04-28T12:00:00.000Z";
    const cookie = {
      identity: { fides_user_device_id: uuid },
      fides_meta: { version: "0.9.0", createdAt: now },
      consent: {},
    };
    cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
    cy.visit("/consent");
    cy.getByTestId("consent");
    cy.overrideSettings({
      IS_OVERLAY_DISABLED: false,
    });
    cy.wait("@getExperience").then((interception) => {
      const { url } = interception.request;
      expect(url).contains(`fides_user_device_id=${uuid}`);
    });
    // Make sure the same uuid propagates to the backend and to the updated cookie
    cy.getByTestId("save-btn").click();
    cy.wait("@patchPrivacyPreference").then((interception) => {
      const { body } = interception.request;
      cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
        const savedCookie = JSON.parse(
          decodeURIComponent(cookieJson!.value)
        ) as FidesCookie;
        expect(body.browser_identity.fides_user_device_id).to.eql(
          savedCookie.identity.fides_user_device_id
        );
      });
    });
  });
});
