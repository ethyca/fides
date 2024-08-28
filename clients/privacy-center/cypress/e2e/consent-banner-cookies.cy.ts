import { CONSENT_COOKIE_NAME, getFidesConsentCookie } from "fides-js";

import { stubConfig } from "../support/stubs";

const domains: {
  domain: string;
  expected: string;
}[] = require("../fixtures/domains.json");

/**
 * This test is for validating our cookie domain logic. We want to ensure that cookies are able to be set on the topmost domain without needing to be the full domain.
 *
 * NOTE: the reason we aren't testing for things like `example` or `example.whatever` is because the browser will *always* set the cookie on *anything* you set for those as long as the page can be visited. This is why `localhost` works for example, or `example.localhost`.
 *
 * For example, if we are on `subdomain.example.co.uk`, we want to be able to set cookies on `example.co.uk` (but not `co.uk`).
 *
 * In order to run this test, you will need to have all of the domains in the `domains.json` set up in your `/etc/hosts` file, for example:
 * 127.0.0.1 example.co.cr
 * 127.0.0.1 subdomain.example.co.cr
 * 127.0.0.1 xyz.subdomain.example.co.cr
 * ...and so forth (unfortunately, wildcard domains are not supported in `/etc/hosts`), as well as one for `example.co.invalid` to test invalid domains.
 *
 * This test will fail if you do not have the domains set up in your `/etc/hosts` file!
 *
 * Once you have the domains set up, you can remove the `.skip` below and run the test.
 */

describe.skip("Consent overlay", () => {
  describe("when visiting valid domains", () => {
    Cypress.on("uncaught:exception", () => false);
    domains.forEach(({ domain, expected }) => {
      it(`allows cookie for ${domain}`, () => {
        Cypress.config("baseUrl", `http://${domain}:3001`);
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
        });
        cy.get("div#fides-banner").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        cy.getCookie(CONSENT_COOKIE_NAME)
          .should("exist")
          .then((cookie) => {
            // check domain of cookie
            expect(cookie?.domain).to.eq(expected);
          });
      });
    });
  });
  describe("when visiting invalid domains", () => {
    it(`doesn't allow cookie for example.co.invalid`, () => {
      Cypress.config("baseUrl", `http://example.co.invalid:3001`);
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
      });
      cy.get("div#fides-banner").within(() => {
        cy.get("button").contains("Opt in to all").click();
      });
      cy.getCookie(CONSENT_COOKIE_NAME)
        .should("exist")
        .then((cookie) => {
          // browser allows this because it assumes it's a localhost domain, which is correct, but the test passes because it's not set to the correct domain `example.co.invalid`
          expect(cookie?.domain).to.eq(".co.invalid");
        });
    });
  });
  describe("when revisiting valid domains", () => {
    Cypress.on("uncaught:exception", () => false);
    domains.forEach(({ domain }) => {
      it(`updates the cookie on the same domain`, () => {
        Cypress.config("baseUrl", `http://${domain}:3001`);
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
        });
        cy.get("div#fides-banner").within(() => {
          cy.get("button").contains("Opt out of all").click();
        });
        cy.getCookie(CONSENT_COOKIE_NAME)
          .should("exist")
          .then(() => {
            const c = getFidesConsentCookie(true);
            expect(c?.fides_meta.consentMethod).to.eq("reject");
          });
        cy.get("button#fides-modal-link").click();
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        cy.getCookie(CONSENT_COOKIE_NAME)
          .should("exist")
          .then(() => {
            const c = getFidesConsentCookie(true);
            expect(c?.fides_meta.consentMethod).to.eq("accept");
          });
      });
    });
  });
});
