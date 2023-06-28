import { createRequest } from "node-mocks-http";

import { lookupGeolocation } from "~/common/geolocation";
import { PrivacyCenterClientSettings } from "~/app/server-environment";

describe("getGeolocation", () => {
  const privacyCenterSettings: PrivacyCenterClientSettings = {
    FIDES_API_URL: "",
    DEBUG: false,
    GEOLOCATION_API_URL: "",
    IS_GEOLOCATION_ENABLED: false,
    IS_OVERLAY_ENABLED: false,
    OVERLAY_PARENT_ID: null,
    MODAL_LINK_ID: null,
    PRIVACY_CENTER_URL: "privacy.example.com",
  };
  describe("when using geolocation headers", () => {
    it("returns geolocation data from country & region headers", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "US",
          "CloudFront-Viewer-Country-Region": "NY",
        },
      });
      const geolocation = lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "US",
        location: "US-NY",
        region: "NY",
      });
    });

    it("returns geolocation data from country header", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "FR",
        },
      });
      const geolocation = lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "FR",
        location: "FR",
      });
    });

    it("ignores only region headers", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country-Region": "NY",
        },
      });
      const geolocation = lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toBeUndefined();
    });

    it("handles invalid geolocation headers", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "Magicland",
        },
      });
      const geolocation = lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toBeUndefined();
    });
  });

  describe("when using ?geolocation query param", () => {
    it("returns geolocation data from query param", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=FR-IDF",
      });
      const geolocation = lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "FR",
        location: "FR-IDF",
        region: "IDF",
      });
    });

    it("handles invalid geolocation query param", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=America",
      });
      const geolocation = lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toBeUndefined();
    });
  });

  describe("when using both headers and query param", () => {
    it("overrides headers with explicit geolocation query param", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=US-CA",
        headers: {
          "CloudFront-Viewer-Country": "FR",
        },
      });
      const geolocation = lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "US",
        location: "US-CA",
        region: "CA",
      });
    });
  });

  describe("when using neither headers nor query param nor geolocation URL", () => {
    it("returns undefined geolocation", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
      });
      const geolocation = lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toBeUndefined();
    });
  });

  describe("when using geolocation URL", () => {
    it("fetches data from geolocation URL", () => {
      privacyCenterSettings.IS_GEOLOCATION_ENABLED = true;
      privacyCenterSettings.GEOLOCATION_API_URL = "some-geolocation-api.com";
      global.fetch = jest.fn(() =>
        Promise.resolve({
          json: () =>
            Promise.resolve({
              country: "US",
              location: "US-CA",
              region: "CA",
            }),
        })
      ) as jest.Mock;
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
      });

      const geolocation = lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "US",
        location: "US-CA",
        region: "CA",
      });
    });
  });
});
