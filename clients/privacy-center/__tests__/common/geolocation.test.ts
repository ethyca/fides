import { createRequest } from "node-mocks-http";

import { lookupGeolocation } from "~/common/geolocation";

describe("getGeolocation", () => {
  describe("when using geolocation headers", () => {
    it("returns geolocation data from country & region headers", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "US",
          "CloudFront-Viewer-Country-Region": "NY",
        },
      });
      const geolocation = await lookupGeolocation(req);
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
      const geolocation = await lookupGeolocation(req);
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
      const geolocation = await lookupGeolocation(req);
      expect(geolocation).toBeNull();
    });

    it("handles invalid geolocation headers", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "Magicland",
        },
      });
      const geolocation = await lookupGeolocation(req);
      expect(geolocation).toBeNull();
    });
  });

  describe("when using ?geolocation query param", () => {
    it("returns geolocation data from query param", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=FR-IDF",
      });
      const geolocation = await lookupGeolocation(req);
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
      const geolocation = await lookupGeolocation(req);
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
      const geolocation = await lookupGeolocation(req);
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
      const geolocation = await lookupGeolocation(req);
      expect(geolocation).toBeNull();
    });
  });
});
