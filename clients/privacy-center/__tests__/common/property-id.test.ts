import { UserGeolocation } from "fides-js";
import { createRequest } from "node-mocks-http";

import { PrivacyCenterEnvironment } from "~/app/server-environment";
import { safeLookupPropertyId } from "~/common/property-id";

describe("safeLookupPropertyId", () => {
  const environment = {
    settings: {
      IS_OVERLAY_ENABLED: true,
      IS_PREFETCH_ENABLED: true,
    },
  } as PrivacyCenterEnvironment;

  const geolocation: UserGeolocation = {};
  const validPropertyId = "FDS-123456";

  it("returns the propertyId when all conditions are met", () => {
    const req = createRequest({
      method: "GET",
      url: "https://privacy.example.com/fides.js",
      query: { property_id: validPropertyId },
    });
    expect(
      safeLookupPropertyId(req as any, geolocation, environment, null),
    ).toBe(validPropertyId);
  });

  it("throws an error if property_id is an array", () => {
    const req = createRequest({
      method: "GET",
      url: "https://privacy.example.com/fides.js",
      query: { property_id: [validPropertyId] },
    });
    expect(() => {
      safeLookupPropertyId(req as any, geolocation, environment, null);
    }).toThrow("Invalid property_id: only one value must be provided.");
  });

  it("throws an error if geolocation is not provided", () => {
    const req = createRequest({
      method: "GET",
      url: "https://privacy.example.com/fides.js",
      query: { property_id: validPropertyId },
    });
    expect(() => {
      safeLookupPropertyId(req as any, null, environment, null);
    }).toThrow("Geolocation must be provided if a property_id is specified.");
  });

  it("throws an error if IS_OVERLAY_ENABLED is false", () => {
    const req = createRequest({
      method: "GET",
      url: "https://privacy.example.com/fides.js",
      query: { property_id: validPropertyId },
    });
    const updatedEnvironment = {
      settings: { ...environment.settings, IS_OVERLAY_ENABLED: false },
    };
    expect(() => {
      safeLookupPropertyId(req as any, geolocation, updatedEnvironment, null);
    }).toThrow(
      "IS_OVERLAY_ENABLED must be enabled in environment settings if a property_id is specified.",
    );
  });

  it("throws an error if IS_PREFETCH_ENABLED is false", () => {
    const req = createRequest({
      method: "GET",
      url: "https://privacy.example.com/fides.js",
      query: { property_id: validPropertyId },
    });
    const updatedEnvironment = {
      settings: { ...environment.settings, IS_PREFETCH_ENABLED: false },
    };
    expect(() => {
      safeLookupPropertyId(req as any, geolocation, updatedEnvironment, null);
    }).toThrow(
      "IS_PREFETCH_ENABLED must be enabled in environment settings if a property_id is specified.",
    );
  });

  it("throws an error if fidesString is provided", () => {
    const req = createRequest({
      method: "GET",
      url: "https://privacy.example.com/fides.js",
      query: { property_id: validPropertyId },
    });
    expect(() => {
      safeLookupPropertyId(
        req as any,
        geolocation,
        environment,
        "mock-fides-string",
      );
    }).toThrow(
      "FIDES_STRING must not be provided if a property_id is specified.",
    );
  });

  it("returns undefined if property_id is not specified", () => {
    const req = createRequest({
      method: "GET",
      url: "https://privacy.example.com/fides.js",
    });
    expect(
      safeLookupPropertyId(req as any, geolocation, environment, null),
    ).toBeUndefined();
  });
});
