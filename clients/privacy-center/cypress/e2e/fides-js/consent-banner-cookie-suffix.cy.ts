import { CONSENT_COOKIE_NAME, FidesCookie } from "fides-js";

import { stubConfig } from "../../support/stubs";

const PRIVACY_NOTICE_KEY_1 = "advertising";
const PRIVACY_NOTICE_KEY_2 = "essential";

describe("Consent cookie with suffix", () => {
  const SUFFIX_1 = "example_company";
  const SUFFIX_2 = "another_company";
  const COOKIE_WITH_SUFFIX_1 = `fides_consent_${SUFFIX_1}`;
  const COOKIE_WITH_SUFFIX_2 = `fides_consent_${SUFFIX_2}`;

  describe("when fides_cookie_suffix query param is provided", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.getCookie(COOKIE_WITH_SUFFIX_1).should("not.exist");
    });

    it("displays the banner on first visit with suffix", () => {
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_1 },
      );

      cy.get("div#fides-banner").should("be.visible");
    });

    it("stores consent in a cookie with the suffix", () => {
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_1 },
      );

      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });

      cy.waitUntilCookieExists(COOKIE_WITH_SUFFIX_1).then(() => {
        cy.getCookie(COOKIE_WITH_SUFFIX_1)
          .should("exist")
          .then((cookie) => {
            const fidesCookie: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            expect(fidesCookie.fides_meta.consentMethod).to.equal("accept");
            expect(fidesCookie.consent[PRIVACY_NOTICE_KEY_1]).to.equal(true);
            expect(fidesCookie.consent[PRIVACY_NOTICE_KEY_2]).to.equal(true);
          });
      });

      // Standard cookie should not exist
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    });

    it("does not show banner on reload with same suffix after consent saved", () => {
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_1 },
      );

      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });

      cy.waitUntilCookieExists(COOKIE_WITH_SUFFIX_1);

      // Reload with same suffix
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_1 },
      );

      cy.waitUntilFidesInitialized();

      // Check if shouldShowExperience() returns the expected value
      cy.window()
        .its("Fides")
        .invoke("shouldShowExperience")
        .should("eql", false);
    });

    it("shows banner when visiting without suffix after saving with suffix", () => {
      // First visit with suffix
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_1 },
      );

      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });

      cy.waitUntilCookieExists(COOKIE_WITH_SUFFIX_1);

      // Visit without suffix - should show banner again
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
      });

      cy.get("div#fides-banner").should("be.visible");
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    });

    it("shows banner when visiting with different suffix", () => {
      // First visit with suffix 1
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_1 },
      );

      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });

      cy.waitUntilCookieExists(COOKIE_WITH_SUFFIX_1);

      // Visit with different suffix - should show banner
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_2 },
      );

      cy.get("div#fides-banner").should("be.visible");
      cy.getCookie(COOKIE_WITH_SUFFIX_2).should("not.exist");
    });

    it("creates separate cookies for different suffixes with different consent values", () => {
      // Set opt-in consent for first suffix
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_1 },
      );

      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });

      cy.waitUntilCookieExists(COOKIE_WITH_SUFFIX_1);

      // Set opt-out consent for second suffix
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_2 },
      );

      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt out of all").click();
      });

      cy.waitUntilCookieExists(COOKIE_WITH_SUFFIX_2);

      // Both cookies should exist with different values
      cy.getCookie(COOKIE_WITH_SUFFIX_1).then((cookie1) => {
        cy.getCookie(COOKIE_WITH_SUFFIX_2).then((cookie2) => {
          const fidesCookie1: FidesCookie = JSON.parse(
            decodeURIComponent(cookie1!.value),
          );
          const fidesCookie2: FidesCookie = JSON.parse(
            decodeURIComponent(cookie2!.value),
          );

          expect(fidesCookie1.fides_meta.consentMethod).to.equal("accept");
          expect(fidesCookie2.fides_meta.consentMethod).to.equal("reject");

          expect(fidesCookie1.consent[PRIVACY_NOTICE_KEY_1]).to.equal(true);
          expect(fidesCookie2.consent[PRIVACY_NOTICE_KEY_1]).to.equal(false);
        });
      });
    });

    it("can update consent for a specific suffix without affecting other suffixes", () => {
      // Set initial consent for both suffixes
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_1 },
      );

      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });

      cy.waitUntilCookieExists(COOKIE_WITH_SUFFIX_1);

      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_2 },
      );

      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });

      cy.waitUntilCookieExists(COOKIE_WITH_SUFFIX_2);

      // Update consent for first suffix only
      stubConfig(
        {
          options: {
            isOverlayEnabled: true,
          },
        },
        undefined,
        undefined,
        { fides_cookie_suffix: SUFFIX_1 },
      );

      cy.waitUntilFidesInitialized().then(() => {
        cy.get("button#fides-modal-link").click();
        cy.getByTestId("fides-modal-content").within(() => {
          cy.get("button").contains("Opt out of all").click();
        });
      });

      cy.wait("@patchPrivacyPreference");

      // Verify first cookie was updated
      cy.getCookie(COOKIE_WITH_SUFFIX_1).then((cookie1) => {
        cy.getCookie(COOKIE_WITH_SUFFIX_2).then((cookie2) => {
          const fidesCookie1: FidesCookie = JSON.parse(
            decodeURIComponent(cookie1!.value),
          );
          const fidesCookie2: FidesCookie = JSON.parse(
            decodeURIComponent(cookie2!.value),
          );

          // First suffix should be rejected now
          expect(fidesCookie1.fides_meta.consentMethod).to.equal("reject");
          // Second suffix should still be accepted
          expect(fidesCookie2.fides_meta.consentMethod).to.equal("accept");
        });
      });
    });
  });

  describe("when fides_cookie_suffix is not provided", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
    });

    it("uses standard cookie name without suffix", () => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
      });

      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });

      cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("exist");
        cy.getCookie(COOKIE_WITH_SUFFIX_1).should("not.exist");
      });
    });
  });
});
