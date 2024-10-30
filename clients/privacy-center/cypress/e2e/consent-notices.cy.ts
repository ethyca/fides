import { CONSENT_COOKIE_NAME, FidesCookie } from "fides-js";

import { ConsentOptionCreate, PrivacyNoticeResponse } from "../../types/api";
import { API_URL } from "../support/constants";

const VERIFICATION_CODE = "112358";
const PRIVACY_NOTICE_ID_1 = "pri_notice-advertising-000";
const PRIVACY_NOTICE_ID_2 = "pri_notice-analytics-000";
const PRIVACY_NOTICE_ID_3 = "pri_notice-essential-000";
const PRIVACY_NOTICE_HISTORY_ID_1 = "pri_notice-history-advertising-en-000";
const PRIVACY_NOTICE_HISTORY_ID_2 = "pri_notice-history-analytics-en-000";
const PRIVACY_NOTICE_HISTORY_ID_3 = "pri_notice-history-essential-en-000";
const PRIVACY_CONFIG_HISTORY_ID = "pri_exp-history-privacy-center-en-000";
const GEOLOCATION_API_URL = "https://www.example.com/location";
const SETTINGS = {
  IS_OVERLAY_ENABLED: true,
  IS_GEOLOCATION_ENABLED: true,
  GEOLOCATION_API_URL,
};

describe("Privacy notice driven consent", () => {
  beforeEach(() => {
    // Seed local storage with verification data
    cy.window().then((win) => {
      win.localStorage.setItem(
        "consentRequestId",
        JSON.stringify("consent-request-id"),
      );
      win.localStorage.setItem(
        "verificationCode",
        JSON.stringify(VERIFICATION_CODE),
      );
    });

    // Set browser language
    cy.on("window:before:load", (win) => {
      Object.defineProperty(win.navigator, "language", {
        value: "en",
      });
    });

    // Intercept sending identity data to the backend to access /consent page
    cy.intercept(
      "POST",
      `${API_URL}/consent-request/consent-request-id/verify`,
      { fixture: "consent/verify" },
    ).as("postConsentRequestVerify");

    // Location intercept
    cy.intercept("GET", GEOLOCATION_API_URL, {
      fixture: "consent/geolocation.json",
    }).as("getGeolocation");

    // Experience intercept
    cy.intercept("GET", `${API_URL}/privacy-experience/*`, {
      fixture: "consent/experience_privacy_center.json",
    }).as("getExperience");

    // Patch privacy preference intercept
    cy.intercept(
      "PATCH",
      `${API_URL}/consent-request/consent-request-id/privacy-preferences*`,
      {
        fixture: "consent/privacy_preferences.json",
      },
    ).as("patchPrivacyPreference");
    // Consent reporting intercept
    cy.intercept(
      "PATCH",
      `${API_URL}/consent-request/consent-request-id/notices-served`,
      { fixture: "consent/notices_served.json" },
    ).as("patchNoticesServed");
  });

  describe("when user has not consented before", () => {
    beforeEach(() => {
      cy.clearAllCookies();
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.visit("/consent");
      cy.getByTestId("consent");
      cy.overrideSettings(SETTINGS);
      cy.getByTestId("consent");
      cy.wait("@getVerificationConfig");
    });

    it("populates its header from the experience config", () => {
      cy.wait("@getExperience");
      cy.getByTestId("consent-heading").contains(
        "Manage your consent preferences",
      );
      cy.getByTestId("consent-description").contains(
        "We use cookies and similar methods",
      );
    });

    it("renders from privacy notices when there is no initial data", () => {
      cy.wait("@postConsentRequestVerify");
      cy.wait("@getExperience").then((interception) => {
        const { url } = interception.request;
        expect(url).contains("region=us_ca");
      });
      cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
        cy.wait("@patchNoticesServed");

        // Opt in, so should default to not checked
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
          cy.getToggle().should("not.be.checked");
        });
        // Opt out, so should default to checked
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_2}`).within(() => {
          cy.getToggle().should("be.checked");
        });
        // Notice only, so should be checked and disabled
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_3}`).within(() => {
          cy.getToggle().should("be.checked").should("be.disabled");
        });

        // Opt in, so should default to not checked
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
          cy.getToggle().should("not.be.checked");
        });
        // Opt out, so should default to checked
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_2}`).within(() => {
          cy.getToggle().should("be.checked");
        });
        // Notice only, so should be checked and disabled
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_3}`).within(() => {
          cy.getToggle().should("be.checked").should("be.disabled");
        });

        // Opt in to the opt in notice
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
          cy.getToggle().should("not.be.checked").check({ force: true });
          cy.getToggle().should("be.checked");
        });
      });

      cy.getByTestId("save-btn").click();
      cy.wait("@patchPrivacyPreference").then((interception) => {
        const { body } = interception.request;
        const {
          preferences,
          code,
          method,
          privacy_experience_config_history_id: id,
        } = body;
        expect(method).to.eql("save");
        expect(code).to.eql(VERIFICATION_CODE);
        expect(id).to.eql(PRIVACY_CONFIG_HISTORY_ID);
        expect(
          preferences.map((p: ConsentOptionCreate) => p.preference),
        ).to.eql(["opt_in", "opt_in", "acknowledge"]);
        // Wait for toast so that we know cookie is ready to be inspected
        cy.get("#toast-1-title").contains(
          "Your consent preferences have been saved",
        );
        // Should update the cookie
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
            const cookie = JSON.parse(
              decodeURIComponent(cookieJson!.value),
            ) as FidesCookie;
            expect(body.browser_identity.fides_user_device_id).to.eql(
              cookie.identity.fides_user_device_id,
            );
            const expectedConsent = {
              advertising: true,
              analytics_opt_out: true,
              essential: true,
            };
            // eslint-disable-next-line @typescript-eslint/naming-convention
            const { consent, fides_meta } = cookie;
            expect(consent).to.eql(expectedConsent);
            expect(fides_meta).to.have.property("createdAt");
            expect(fides_meta).to.have.property("updatedAt");
            expect(fides_meta).to.have.property("consentMethod", "save");
            // Should update the window object
            cy.window().then((win) => {
              expect(win.Fides.consent).to.eql(expectedConsent);
            });
          });
        });
      });
    });

    it("uses the device id found in an already existing cookie", () => {
      cy.wait("@getExperience");
      const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
      const createdAt = "2023-04-28T12:00:00.000Z";
      const updatedAt = "2023-04-29T12:00:00.000Z";
      const cookie = {
        identity: { fides_user_device_id: uuid },
        fides_meta: { version: "0.9.0", createdAt, updatedAt },
        consent: {},
      };
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));

      // Make sure the same uuid propagates to the backend and to the updated cookie
      cy.getByTestId("save-btn").click();
      cy.wait("@patchPrivacyPreference").then((interception) => {
        const { body } = interception.request;
        cy.getCookie(CONSENT_COOKIE_NAME).then((cookieJson) => {
          const savedCookie = JSON.parse(
            decodeURIComponent(cookieJson!.value),
          ) as FidesCookie;
          expect(body.browser_identity.fides_user_device_id).to.eql(
            savedCookie.identity.fides_user_device_id,
          );
        });
      });
    });

    describe("cookie enforcement", () => {
      beforeEach(() => {
        // First seed the browser with the cookies that are listed in the notices
        cy.fixture("consent/experience_privacy_center.json").then((data) => {
          const notices: PrivacyNoticeResponse[] =
            data.items[0].privacy_notices;

          const allCookies = notices.map((notice) => notice.cookies).flat();
          allCookies.forEach((cookie) => {
            cy.setCookie(cookie.name, "value", {
              path: cookie.path ?? "/",
              domain: cookie.domain ?? undefined,
            });
          });
          cy.getAllCookies().then((cookies) => {
            expect(
              cookies.filter((c) => c.name !== CONSENT_COOKIE_NAME).length,
            ).to.eql(allCookies.length);
          });
          cy.wrap(notices).as("notices");
        });
      });

      it("can delete all cookies for when opting out of all notices", () => {
        // Opt out of the opt-out notice
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_2}`).within(() => {
          cy.getToggle().should("be.checked");
          cy.getToggle().uncheck();
        });
        cy.getByTestId("save-btn").click();

        cy.wait("@patchPrivacyPreference").then(() => {
          // Use waitUntil to help with CI
          cy.waitUntil(() =>
            cy.getAllCookies().then((cookies) => cookies.length === 1),
          ).then(() => {
            // There should be no cookies related to the privacy notices around
            cy.getAllCookies().then((cookies) => {
              const filteredCookies = cookies.filter(
                (c) => c.name !== CONSENT_COOKIE_NAME,
              );
              expect(filteredCookies.length).to.eql(0);
            });
          });
        });
      });

      it("can delete only the cookies associated with opt-out notices", () => {
        // Opt into first notice
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
          cy.getToggle().check();
        });
        // Opt out of second notice
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_2}`).within(() => {
          cy.getToggle().should("be.checked");
          cy.getToggle().uncheck();
        });
        cy.getByTestId("save-btn").click();

        cy.wait("@patchPrivacyPreference").then(() => {
          // Use waitUntil to help with CI
          cy.waitUntil(() =>
            cy.getAllCookies().then((cookies) => cookies.length === 2),
          ).then(() => {
            // The first notice's cookies should still be around
            // But there should be none of the second cookie's
            cy.getAllCookies().then((cookies) => {
              const filteredCookies = cookies.filter(
                (c) => c.name !== CONSENT_COOKIE_NAME,
              );
              expect(filteredCookies.length).to.eql(1);
              cy.get("@notices").then((notices: any) => {
                expect(filteredCookies[0]).to.have.property(
                  "name",
                  notices[0].cookies[0].name,
                );
              });
            });
          });
        });
      });

      it("can successfully delete even if cookie does not exist", () => {
        cy.clearAllCookies();
        // Opt out of second notice
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_2}`).within(() => {
          cy.getToggle().should("be.checked");
          cy.getToggle().uncheck();
        });
        cy.getByTestId("save-btn").click();

        cy.wait("@patchPrivacyPreference").then(() => {
          cy.getAllCookies().then((cookies) => {
            const filteredCookies = cookies.filter(
              (c) => c.name !== CONSENT_COOKIE_NAME,
            );
            expect(filteredCookies.length).to.eql(0);
          });
        });
      });
    });
  });

  describe("when user has consented before", () => {
    it("renders from privacy notices when user has consented before", () => {
      const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
      const createdAt = "2023-04-28T12:00:00.000Z";
      const updatedAt = "2023-04-29T12:00:00.000Z";
      const cookie = {
        identity: { fides_user_device_id: uuid },
        fides_meta: { version: "0.9.0", createdAt, updatedAt },
        consent: {
          advertising: true,
          analytics_opt_out: false,
          essential: true,
        },
      };
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
      // Visit the consent page with notices enabled
      cy.visit("/consent");
      cy.getByTestId("consent");
      cy.overrideSettings(SETTINGS);
      // Should follow state of consent cookie
      cy.wait("@getExperience").then(() => {
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_1}`).within(() => {
          cy.getToggle().should("be.checked");
        });
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_2}`).within(() => {
          cy.getToggle().should("not.be.checked");
        });
        cy.getByTestId(`consent-item-${PRIVACY_NOTICE_ID_3}`).within(() => {
          cy.getToggle().should("be.checked");
        });
      });

      cy.getByTestId("save-btn").click();
      cy.wait("@patchPrivacyPreference").then((interception) => {
        const { body } = interception.request;
        const { preferences } = body;
        expect(
          preferences.map((p: ConsentOptionCreate) => p.preference),
        ).to.eql(["opt_in", "opt_out", "acknowledge"]);
      });
    });
  });

  describe("consent reporting", () => {
    beforeEach(() => {
      cy.visit("/consent");
      cy.getByTestId("consent");
      cy.overrideSettings(SETTINGS);
    });

    it("can make calls to consent reporting endpoints", () => {
      cy.wait("@patchNoticesServed").then((interception) => {
        expect(interception.request.body.privacy_notice_history_ids).to.eql([
          PRIVACY_NOTICE_HISTORY_ID_1,
          PRIVACY_NOTICE_HISTORY_ID_2,
          PRIVACY_NOTICE_HISTORY_ID_3,
        ]);
        cy.getByTestId("save-btn").click();
        cy.wait("@patchPrivacyPreference").then((preferenceInterception) => {
          // eslint-disable-next-line @typescript-eslint/naming-convention
          const { served_notice_history_id } =
            preferenceInterception.request.body;
          const expected = interception.response?.body.served_notice_history_id;
          expect(served_notice_history_id).to.eql(expected);
        });
      });
    });
  });

  describe("Hierarchical notices (notices with children)", () => {
    beforeEach(() => {
      // Experience intercept
      cy.intercept("GET", `${API_URL}/privacy-experience/*`, {
        fixture: "consent/experience_privacy_center_hierarchical.json",
      }).as("getExperience");
    });

    it("renders hierarchical notices correctly", () => {
      cy.visit("/consent");
      cy.getByTestId("consent");
      cy.overrideSettings(SETTINGS);
      cy.wait("@getExperience");

      cy.getByTestId("consent-item-pri_notice-advertising-000").within(() => {
        // Child items
        cy.getByTestId("toggle-Weekly Newsletter").should("exist");
        cy.getByTestId("toggle-Monthly Newsletter").should("exist");
      });

      cy.getByTestId("consent-item-pri_notice-analytics-000");
      cy.getByTestId("consent-item-pri_notice-essential-000");
    });

    it("parent toggle should toggle all children", () => {
      cy.visit("/consent");
      cy.getByTestId("consent");
      cy.overrideSettings(SETTINGS);
      cy.wait("@getExperience");

      cy.getByTestId("consent-item-pri_notice-advertising-000")
        .click()
        .within(() => {
          cy.getByTestId("toggle-Advertising").should("not.be.checked");
          cy.getByTestId("toggle-Weekly Newsletter")
            .getToggle()
            .should("not.be.checked");
          cy.getByTestId("toggle-Monthly Newsletter")
            .getToggle()
            .should("not.be.checked");

          cy.getByTestId("toggle-Advertising").getToggle().check();
          cy.getByTestId("toggle-Weekly Newsletter")
            .getToggle()
            .should("be.checked");
          cy.getByTestId("toggle-Monthly Newsletter")
            .getToggle()
            .should("be.checked");

          cy.getByTestId("toggle-Advertising").getToggle().uncheck();
          cy.getByTestId("toggle-Weekly Newsletter")
            .getToggle()
            .should("not.be.checked");
          cy.getByTestId("toggle-Monthly Newsletter")
            .getToggle()
            .should("not.be.checked");
        });
    });

    it("toggle all children should toggle parent", () => {
      cy.visit("/consent");
      cy.getByTestId("consent");
      cy.overrideSettings(SETTINGS);
      cy.wait("@getExperience");

      cy.getByTestId("consent-item-pri_notice-advertising-000")
        .click()
        .within(() => {
          cy.getByTestId("toggle-Advertising")
            .getToggle()
            .should("not.be.checked");
          cy.getByTestId("toggle-Weekly Newsletter")
            .getToggle()
            .should("not.be.checked");
          cy.getByTestId("toggle-Monthly Newsletter")
            .getToggle()
            .should("not.be.checked");

          cy.getByTestId("toggle-Weekly Newsletter").getToggle().check();
          cy.getByTestId("toggle-Monthly Newsletter").getToggle().check();

          cy.getByTestId("toggle-Advertising").getToggle().should("be.checked");
        });
    });

    it("can save hierarchical notices", () => {
      cy.visit("/consent");
      cy.getByTestId("consent");
      cy.overrideSettings(SETTINGS);
      cy.wait("@getExperience");

      cy.getByTestId("consent-item-pri_notice-advertising-000").click();
      cy.getByTestId("toggle-Weekly Newsletter").getToggle().check();
      cy.getByTestId("toggle-Monthly Newsletter").getToggle().check();

      cy.getByTestId("save-btn").click();

      cy.wait("@patchPrivacyPreference").then((interception) => {
        const { preferences } = interception.request.body;

        const CHILD_PRIVACY_NOTICE_HISTORY_ID_1 =
          "pri_notice-weekly-newsletter-advertising-en-001";
        const CHILD_PRIVACY_NOTICE_HISTORY_ID_2 =
          "pri_notice-monthly-newsletter-advertising-en-001";

        const expected = [
          {
            preference: "opt_in",
            privacy_notice_history_id: PRIVACY_NOTICE_HISTORY_ID_1,
          },
          {
            preference: "opt_in",
            privacy_notice_history_id: CHILD_PRIVACY_NOTICE_HISTORY_ID_1,
          },
          {
            preference: "opt_in",
            privacy_notice_history_id: CHILD_PRIVACY_NOTICE_HISTORY_ID_2,
          },
          {
            preference: "opt_in",
            privacy_notice_history_id: PRIVACY_NOTICE_HISTORY_ID_2,
          },
          {
            preference: "acknowledge",
            privacy_notice_history_id: PRIVACY_NOTICE_HISTORY_ID_3,
          },
        ];
        expect(preferences).to.eql(expected);
      });
    });
  });
});
