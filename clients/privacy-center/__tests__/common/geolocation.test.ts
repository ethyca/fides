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
      const geolocation = await lookupGeolocation(req as any);
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
      const geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toEqual({
        country: "FR",
        location: "FR",
      });
    });

    it("supports the special 'EEA' code in country header", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "EEA",
        },
      });
      const geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toEqual({
        country: "EEA",
        location: "EEA",
      });
    });

    it("ignores only region headers", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country-Region": "NY",
        },
      });
      const geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toBeNull();
    });

    it("ignores invalid geolocation headers", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "Magicland",
        },
      });
      const geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toBeNull();
    });

    it("ignores invalid three-character country geolocation headers", async () => {
      let req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "USA",
        },
      });
      let geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toBeNull();

      // Test again including a (seemingly valid!) region
      req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "USA-NY",
        },
      });
      geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toBeNull();
    });

    it("ignores invalid, numeric country geolocation headers", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "00",
        },
      });
      const geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toBeNull();
    });

    it("discards invalid region geolocation headers", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js",
        headers: {
          "CloudFront-Viewer-Country": "US",
          "CloudFront-Viewer-Country-Region": "NewYork",
        },
      });
      const geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toEqual({
        country: "US",
        location: "US",
      });
    });

    it("handles various ISO-3166 edge cases (numeric regions, single-character codes, etc.)", async () => {
      const tests = [
        { input: { country: "US", region: undefined }, expected: "US" },
        { input: { country: "us", region: undefined }, expected: "us" },
        { input: { country: "SE", region: "O" }, expected: "SE-O" },
        { input: { country: "gb", region: "eng" }, expected: "gb-eng" },
        { input: { country: "RU", region: "PRI" }, expected: "RU-PRI" },
        { input: { country: "TR", region: "09" }, expected: "TR-09" },
        { input: { country: "BF", region: "03" }, expected: "BF-03" },
        { input: { country: "CZ", region: "321" }, expected: "CZ-321" },
        { input: { country: "EEA", region: undefined }, expected: "EEA" },
      ];
      return Promise.all(
        tests.map(async (value) => {
          const { input, expected } = value;
          const req = createRequest({
            url: "https://privacy.example.com/fides.js",
            headers: {
              "CloudFront-Viewer-Country": input.country,
              "CloudFront-Viewer-Country-Region": input.region,
            },
          });
          const geolocation = await lookupGeolocation(req as any);
          expect(geolocation).toEqual({
            country: input.country,
            region: input.region,
            location: expected,
          });
        }),
      );
    });
  });

  describe("when using ?geolocation query param", () => {
    it("returns geolocation data from query param", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=FR-IDF",
      });
      const geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toEqual({
        country: "FR",
        location: "FR-IDF",
        region: "IDF",
      });
    });

    it("supports the special 'EEA' code in geolocation query param", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=EEA",
      });
      const geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toEqual({
        country: "EEA",
        location: "EEA",
      });
    });

    it("ignores invalid geolocation query param", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=America",
      });
      await expect(lookupGeolocation(req as any)).rejects.toThrow(
        "Provided location (America) query parameter is not in ISO 3166 format.",
      );
    });

    it("ignores invalid three-character country codes in geolocation query param", async () => {
      let req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=USA",
      });
      await expect(lookupGeolocation(req as any)).rejects.toThrow(
        "Provided location (USA) query parameter is not in ISO 3166 format.",
      );

      // Test again including a (seemingly valid!) region
      req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=USA-NY",
      });
      await expect(lookupGeolocation(req as any)).rejects.toThrow(
        "Provided location (USA-NY) query parameter is not in ISO 3166 format.",
      );
    });

    it("ignores invalid, numeric geolocation query param", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=12",
      });
      await expect(lookupGeolocation(req as any)).rejects.toThrow(
        "Provided location (12) query parameter is not in ISO 3166 format.",
      );
    });

    it("ignores invalid, partial locations from geolocation query param (e.g. 'US-')", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=US-",
      });
      await expect(lookupGeolocation(req as any)).rejects.toThrow(
        "Provided location (US-) query parameter is not in ISO 3166 format.",
      );
    });

    it("ignores invalid regions from geolocation query param (e.g. 'US-NewYork')", async () => {
      const req = createRequest({
        url: "https://privacy.example.com/fides.js?geolocation=US-NewYork",
      });
      await expect(lookupGeolocation(req as any)).rejects.toThrow(
        "Provided location (US-NewYork) query parameter is not in ISO 3166 format.",
      );
    });

    it("handles various ISO-3166 edge cases (numeric regions, single-character codes, etc.)", async () => {
      const tests = [
        {
          input: "US",
          expected: { location: "US", country: "US", region: undefined },
        },
        {
          input: "us",
          expected: { location: "us", country: "us", region: undefined },
        },
        {
          input: "SE-O",
          expected: { location: "SE-O", country: "SE", region: "O" },
        },
        {
          input: "gb-eng",
          expected: { location: "gb-eng", country: "gb", region: "eng" },
        },
        {
          input: "RU-PRI",
          expected: { location: "RU-PRI", country: "RU", region: "PRI" },
        },
        {
          input: "TR-09",
          expected: { location: "TR-09", country: "TR", region: "09" },
        },
        {
          input: "BF-03",
          expected: { location: "BF-03", country: "BF", region: "03" },
        },
        {
          input: "CZ-321",
          expected: { location: "CZ-321", country: "CZ", region: "321" },
        },
        {
          input: "EEA",
          expected: { location: "EEA", country: "EEA", region: undefined },
        },
      ];
      return Promise.all(
        tests.map(async (value) => {
          const { input, expected } = value;
          const req = createRequest({
            url: `https://privacy.example.com/fides.js?geolocation=${input}`,
          });
          const geolocation = await lookupGeolocation(req as any);
          expect(geolocation).toEqual({
            country: expected.country,
            region: expected.region,
            location: expected.location,
          });
        }),
      );
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
      const geolocation = await lookupGeolocation(req as any);
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
      const geolocation = await lookupGeolocation(req as any);
      expect(geolocation).toBeNull();
    });
  });
});
