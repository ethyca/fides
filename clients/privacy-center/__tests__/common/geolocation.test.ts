import { createRequest } from "node-mocks-http";
import requestIp from "request-ip";

import { lookupGeolocation } from "~/common/geolocation";
import { PrivacyCenterClientSettings } from "~/app/server-environment";

describe("getGeolocation", () => {
  const privacyCenterSettings: PrivacyCenterClientSettings = {
    FIDES_API_URL: "",
    SERVER_SIDE_FIDES_API_URL: "",
    DEBUG: false,
    GEOLOCATION_API_URL: "",
    IS_GEOLOCATION_ENABLED: false,
    IS_OVERLAY_ENABLED: false,
    IS_PREFETCH_ENABLED: false,
    TCF_ENABLED: false,
    OVERLAY_PARENT_ID: null,
    MODAL_LINK_ID: null,
    PRIVACY_CENTER_URL: "privacy.example.com",
  };
  describe("when using geolocation headers", () => {
    it("returns geolocation data from country & region headers", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "US",
          "CloudFront-Viewer-Country-Region": "NY",
        },
      });
      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "US",
        location: "US-NY",
        region: "NY",
      });
    });

    it("returns geolocation data from country header", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "FR",
        },
      });
      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "FR",
        location: "FR",
      });
    });

    it("ignores only region headers", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country-Region": "NY",
        },
      });
      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toBeNull();
    });

    it("handles invalid geolocation headers", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "Magicland",
        },
      });
      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toBeNull();
    });
  });

  describe("when using ?geolocation query param", () => {
    it("returns geolocation data from query param", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=FR-IDF",
      });
      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "FR",
        location: "FR-IDF",
        region: "IDF",
      });
    });

    it("handles invalid geolocation query param", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=America",
      });
      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toBeNull();
    });
  });

  describe("when using both headers and query param", () => {
    it("overrides headers with explicit geolocation query param", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=US-CA",
        headers: {
          "CloudFront-Viewer-Country": "FR",
        },
      });
      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "US",
        location: "US-CA",
        region: "CA",
      });
    });
  });

  describe("when using neither headers nor query param nor geolocation URL", () => {
    it("returns undefined geolocation", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
      });
      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toBeNull();
    });
  });

  describe("when using geolocation URL", () => {
    it("fetches data from geolocation URL when ip is detected using cloudfront header", async () => {
      privacyCenterSettings.IS_GEOLOCATION_ENABLED = true;
      privacyCenterSettings.GEOLOCATION_API_URL = "some-geolocation-api.com";
      privacyCenterSettings.IS_OVERLAY_ENABLED = true;
      privacyCenterSettings.IS_PREFETCH_ENABLED = true;
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
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
        headers: {
          "cloudfront-viewer-address": "123.456.778",
        },
      });

      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "US",
        location: "US-CA",
        region: "CA",
      });
    });

    it("fetches data from geolocation URL when ip is detected using library", async () => {
      privacyCenterSettings.IS_GEOLOCATION_ENABLED = true;
      privacyCenterSettings.GEOLOCATION_API_URL = "some-geolocation-api.com";
      privacyCenterSettings.IS_OVERLAY_ENABLED = true;
      privacyCenterSettings.IS_PREFETCH_ENABLED = true;
      const testIp = "123.456.778";
      jest.mock("request-ip");
      requestIp.getClientIp = jest.fn().mockReturnValue(testIp);
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
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

      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual({
        country: "US",
        location: "US-CA",
        region: "CA",
      });
    });

    it("does not fetch data from geolocation URL when ip is not detected", async () => {
      privacyCenterSettings.IS_GEOLOCATION_ENABLED = true;
      privacyCenterSettings.GEOLOCATION_API_URL = "some-geolocation-api.com";
      privacyCenterSettings.IS_OVERLAY_ENABLED = true;
      privacyCenterSettings.IS_PREFETCH_ENABLED = true;
      jest.mock("request-ip");
      requestIp.getClientIp = jest.fn().mockReturnValue(null);
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
      });

      const geolocation = await lookupGeolocation(req, privacyCenterSettings);
      expect(geolocation).toEqual(null);
    });
  });
});
