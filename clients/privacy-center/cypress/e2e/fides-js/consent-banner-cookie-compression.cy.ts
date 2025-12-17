import { CONSENT_COOKIE_NAME } from "fides-js";
import { stubConfig } from "support/stubs";

describe("when fidesCookieCompression is set to 'gzip'", () => {
  it("verifies CompressionStream API is available in test browser", () => {
    cy.window().then((win) => {
      // Verify the browser APIs we rely on are available
      expect(win.CompressionStream).to.exist;
      expect(win.DecompressionStream).to.exist;
    });
  });

  it("saves cookies with gzip compression", () => {
    stubConfig({
      options: {
        fidesCookieCompression: "gzip",
      },
    });

    cy.get("div#fides-banner").within(() => {
      cy.get("button").contains("Opt in to all").click();
    });

    cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
      expect(cookie).to.exist;
      // Cookie value is URL-encoded, so decode first
      const decodedValue = decodeURIComponent(cookie!.value);
      // Should have gzip: prefix
      expect(decodedValue).to.match(/^gzip:/);
      // Should NOT be parseable as JSON (it's compressed)
      expect(() => JSON.parse(decodedValue)).to.throw;
    });
  });

  it("can read back compressed cookies correctly", () => {
    stubConfig({
      options: {
        isOverlayEnabled: true,
        fidesCookieCompression: "gzip",
      },
    });

    // Save consent
    cy.get("div#fides-banner").within(() => {
      cy.get("button").contains("Opt in to all").click();
    });

    // Wait for cookie to be saved
    cy.waitUntilCookieExists(CONSENT_COOKIE_NAME);

    // Verify the cookie is compressed
    cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
      const decodedValue = decodeURIComponent(cookie!.value);
      expect(decodedValue).to.match(/^gzip:/);
    });

    // Reload the page - if decompression fails, banner would reappear
    cy.reload();

    // If decompression worked, banner should not reappear (consent was read successfully)
    cy.get("div#fides-banner").should("not.exist");

    // Cookie should still be compressed
    cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
      const decodedValue = decodeURIComponent(cookie!.value);
      expect(decodedValue).to.match(/^gzip:/);
    });
  });

  it("maintains compression when updating preferences via modal", () => {
    stubConfig({
      options: {
        isOverlayEnabled: true,
        fidesCookieCompression: "gzip",
      },
    });

    // Initial opt-in
    cy.get("div#fides-banner").within(() => {
      cy.get("button").contains("Opt in to all").click();
    });

    // Wait for cookie to be saved
    cy.waitUntilCookieExists(CONSENT_COOKIE_NAME);

    // Verify initial cookie is compressed
    cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
      const decodedValue = decodeURIComponent(cookie!.value);
      expect(decodedValue).to.match(/^gzip:/);
    });

    // Open modal to change preferences
    cy.get("#fides-modal-link").click();
    cy.getByTestId("consent-modal").should("be.visible");

    // Change a preference toggle
    cy.getByTestId("toggle-Advertising").within(() => {
      cy.get("input").click();
    });

    // Save changes
    cy.getByTestId("consent-modal").within(() => {
      cy.get("button").contains("Save").click();
    });

    // Verify updated cookie is still compressed
    cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
      const decodedValue = decodeURIComponent(cookie!.value);
      expect(decodedValue).to.match(/^gzip:/);
    });
  });
});
