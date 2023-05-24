import { createRequest } from "node-mocks-http";

import { getGeolocation } from "~/common/geolocation";

describe("getGeolocation", () => {
  describe("when using geolocation headers", () => {
    it("returns geolocation data from country & region headers", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "US",
          "CloudFront-Viewer-Country-Region": "NY",
        },
      });
      const geolocation = getGeolocation(req);
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
      const geolocation = getGeolocation(req);
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
      const geolocation = getGeolocation(req);
      expect(geolocation).toBeUndefined();
    });

    it("handles invalid geolocation headers", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "Magicland",
        },
      });
      const geolocation = getGeolocation(req);
      expect(geolocation).toBeUndefined();
    });
  });

  describe("when using ?geolocation query param", () => {
    it("returns geolocation data from query param", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=FR-IDF",
      });
      const geolocation = getGeolocation(req);
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
      const geolocation = getGeolocation(req);
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
      const geolocation = getGeolocation(req);
      expect(geolocation).toEqual({
        country: "US",
        location: "US-CA",
        region: "CA",
      });
    });
  });

  describe("when using neither headers nor query param", () => {
    it("returns undefined geolocation", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
      });
      const geolocation = getGeolocation(req);
      expect(geolocation).toBeUndefined();
    });
  });
});
