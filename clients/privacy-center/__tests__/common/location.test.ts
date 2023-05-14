import { createRequest } from "node-mocks-http";

import { getLocation } from "~/common/location";

describe("getLocation", () => {
  describe("when using location headers", () => {
    it("returns location data from country & region headers", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "US",
          "CloudFront-Viewer-Country-Region": "NY",
        },
      });
      const location = getLocation(req);
      expect(location).toEqual({
        country: "US",
        location: "US-NY",
        region: "NY",
      });
    });

    it("returns location data from country header", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "FR",
        },
      });
      const location = getLocation(req);
      expect(location).toEqual({
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
      const location = getLocation(req);
      expect(location).toBeUndefined();
    });

    it("handles invalid location headers", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "Magicland",
        },
      });
      const location = getLocation(req);
      expect(location).toBeUndefined();
    });
  });

  describe("when using ?location query param", () => {
    it("returns location data from query param", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?location=FR-IDF",
      });
      const location = getLocation(req);
      expect(location).toEqual({
        country: "FR",
        location: "FR-IDF",
        region: "IDF",
      });
    });

    it("handles invalid location query param", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?location=America",
      });
      const location = getLocation(req);
      expect(location).toBeUndefined();
    });
  });

  describe("when using both headers and query param", () => {
    it("overrides headers with explicit location query param", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?location=US-CA",
        headers: {
          "CloudFront-Viewer-Country": "FR",
        },
      });
      const location = getLocation(req);
      expect(location).toEqual({
        country: "US",
        location: "US-CA",
        region: "CA",
      });
    });
  });

  describe("when using neither headers nor query param", () => {
    it("returns undefined location", () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
      });
      const location = getLocation(req);
      expect(location).toBeUndefined();
    });
  });
});
