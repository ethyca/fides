import { OVERRIDE, stubConfig } from "../support/stubs";

describe("Consent banner with vendor asset disclosure", () => {
  beforeEach(() => {
    cy.fixture("consent/experience_vendor_disclosure.json").then((payload) => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
        experience: payload,
      });
    });
  });

  it("does not show the vendors link when the feature is disabled", () => {
    cy.fixture("consent/experience_vendor_disclosure.json").then((payload) => {
      payload.experience_config.allow_vendor_asset_disclosure = false;
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
        experience: payload,
      });
    });
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("div#fides-banner").should("be.visible");
      cy.get("button").contains("Manage preferences").click();
      cy.contains(".fides-notice-toggle", "Advertising").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendors-disclosure-link").should("not.exist");
      });
    });
  });

  it("does not show the vendors link when asset type is not included", () => {
    cy.fixture("consent/experience_vendor_disclosure.json").then((payload) => {
      payload.experience_config.asset_disclosure_include_types = [];
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
        experience: payload,
      });
    });
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("div#fides-banner").should("be.visible");
      cy.get("button").contains("Manage preferences").click();
      cy.contains(".fides-notice-toggle", "Advertising").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendors-disclosure-link").should("not.exist");
      });
    });
  });

  it("does not show the vendors link when no assets are associated", () => {
    cy.fixture("consent/experience_vendor_disclosure.json").then((payload) => {
      payload.privacy_notices[0].cookies = [];
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
        experience: payload,
      });
    });
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("div#fides-banner").should("be.visible");
      cy.get("button").contains("Manage preferences").click();
      cy.contains(".fides-notice-toggle", "Advertising").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendors-disclosure-link").should("not.exist");
      });
    });
  });

  it("shows the vendors link when the feature is enabled", () => {
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("div#fides-banner").should("be.visible");
      cy.get("button").contains("Manage preferences").click();
      cy.contains(".fides-notice-toggle", "Advertising").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendors-disclosure-link").should("be.visible");
      });
    });
  });

  it("can navigate to the vendor disclosure view and back", () => {
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("div#fides-banner").should("be.visible");
      cy.get("button").contains("Manage preferences").click();
      cy.contains(".fides-notice-toggle", "Advertising").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendors-disclosure-link").click();
      });
      cy.get(".fides-modal-content").contains("Vendors");
      cy.get(".fides-back-link").click();
      cy.get(".fides-modal-content").contains(
        "Manage your consent preferences",
      );
    });
  });

  it("displays vendors and their cookies", () => {
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("div#fides-banner").should("be.visible");
      cy.get("button").contains("Manage preferences").click();
      cy.contains(".fides-notice-toggle", "Advertising").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendors-disclosure-link").click();
      });
      cy.contains(".fides-notice-toggle", "Example Vendor").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendor-details-table").contains("vendor_cookie");
        cy.get(".fides-vendor-details-table").contains("1 year");
      });
    });
  });

  it("does not show description when cookie has no description", () => {
    cy.fixture("consent/experience_vendor_disclosure.json").then((payload) => {
      payload.privacy_notices[0].cookies[0].description = undefined;
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
        experience: payload,
      });
    });
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("div#fides-banner").should("be.visible");
      cy.get("button").contains("Manage preferences").click();
      cy.contains(".fides-notice-toggle", "Advertising").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendors-disclosure-link").click();
      });
      cy.contains(".fides-notice-toggle", "Example Vendor").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendor-details-table").contains("vendor_cookie");
        cy.get(".fides-vendor-details-table").should(
          "not.contain",
          "Description",
        );
      });
    });
  });

  it("displays multiple vendors and cookies", () => {
    cy.fixture("consent/experience_vendor_disclosure.json").then((payload) => {
      payload.privacy_notices[0].cookies.push({
        name: "another_cookie",
        system_name: "Another Vendor",
      });
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
        experience: payload,
      });
    });
    cy.waitUntilFidesInitialized().then(() => {
      cy.get("div#fides-banner").should("be.visible");
      cy.get("button").contains("Manage preferences").click();
      cy.contains(".fides-notice-toggle", "Advertising").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendors-disclosure-link").click();
      });
      cy.contains(".fides-notice-toggle", "Example Vendor").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendor-details-table").contains("vendor_cookie");
      });
      cy.contains(".fides-notice-toggle", "Another Vendor").within(() => {
        cy.get(".fides-notice-toggle-trigger").click();
        cy.get(".fides-vendor-details-table").contains("another_cookie");
      });
    });
  });

  it("sends the disabled systems to the API", () => {
    cy.fixture("consent/experience_vendor_disclosure.json").then((payload) => {
      const geoLocationUrl = "https://some-geolocation-api.com";
      stubConfig({
        experience: OVERRIDE.UNDEFINED,
        geolocation: OVERRIDE.UNDEFINED,
        options: {
          isGeolocationEnabled: true,
          geolocationApiUrl: geoLocationUrl,
          isOverlayEnabled: true,
          fidesDisabledSystems: ["Example Vendor", "Another Vendor"],
        },
      });
    });
    cy.waitUntilFidesInitialized().then(() => {
      cy.wait("@getPrivacyExperience").then((interception) => {
        const url = new URL(interception.request.url);
        expect(url.searchParams.get("exclude_notice_assets_by_systems")).to.eq(
          "Another Vendor,Example Vendor", // Alphabetic deterministic order
        );
      });
    });
  });
});
