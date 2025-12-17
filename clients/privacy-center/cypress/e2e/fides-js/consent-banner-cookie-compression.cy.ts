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
        isOverlayEnabled: true,
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

    // Verify the cookie was compressed
    cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
      const decodedValue = decodeURIComponent(cookie!.value);
      expect(decodedValue).to.match(/^gzip:/);
    });

    // Reload the page to verify decompression works
    cy.reload();

    // Verify Fides can read the compressed cookie
    cy.window().its("Fides").its("consent").should("exist");
    cy.window().its("Fides").its("consent").should("deep.include", {
      data_sales: true,
      tracking: true,
    });
  });

  it("handles modal interactions with compressed cookies", () => {
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

    // Wait for banner to close
    cy.get("div#fides-banner").should("not.exist");

    // Open modal to change preferences
    cy.get("#fides-modal-link").click();
    cy.get("div#fides-modal-content").within(() => {
      cy.get("button").contains("Opt out of all").click();
    });

    // Verify updated cookie is still compressed
    cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
      const decodedValue = decodeURIComponent(cookie!.value);
      expect(decodedValue).to.match(/^gzip:/);
    });

    // Verify consent was updated
    cy.window().its("Fides").its("consent").should("deep.include", {
      data_sales: false,
      tracking: false,
    });
  });
});
