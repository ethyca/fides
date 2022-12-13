import { describe, expect, it } from "@jest/globals";

import { configureZones, resolveZone } from "~/features/common/zones";

describe("resolveZone", () => {
  // Allow mocking and resetting the node env in this test suite.
  const env = process.env as { NODE_ENV: string };
  afterEach(() => {
    env.NODE_ENV = "test";
  });

  const config = configureZones({
    development: {
      host: "localhost:3000",
    },

    zones: [
      {
        basePath: "/datamap",
        development: {
          host: "localhost:4000",
        },
      },
      {
        basePath: "/no/dev",
      },
    ],
  });

  describe("Within the root zone", () => {
    const basePath = "/";

    it("Does not modify a link within the root zone", () => {
      env.NODE_ENV = "development";

      const link = resolveZone({ config, basePath, href: "/root/route" });
      expect(link).toMatchObject({
        href: "/root/route",
        basePath: "/",
      });
    });

    it("Links to the dev host of another zone", () => {
      env.NODE_ENV = "development";

      const link = resolveZone({ config, basePath, href: "/datamap" });
      expect(link).toMatchObject({
        href: "http://localhost:4000/datamap",
        basePath: "/datamap",
      });
    });

    it("Does not link to the dev host in production", () => {
      env.NODE_ENV = "production";

      const link = resolveZone({ config, basePath, href: "/datamap" });
      expect(link).toMatchObject({
        href: "/datamap",
        basePath: "/datamap",
      });
    });

    it("Does not link to the dev host if none is configured", () => {
      env.NODE_ENV = "development";

      const link = resolveZone({ config, basePath, href: "/no/dev" });
      expect(link).toMatchObject({
        href: "/no/dev",
        basePath: "/no/dev",
      });
    });
  });

  describe("Within a sub zone", () => {
    const basePath = "/datamap";

    it("Strips the base path of the sub-zone", () => {
      const link = resolveZone({ config, basePath, href: "/datamap/route" });
      expect(link).toMatchObject({
        href: "/route",
        basePath: "/datamap",
      });
    });

    it("Links to the dev host of the root zone", () => {
      env.NODE_ENV = "development";

      const link = resolveZone({ config, basePath, href: "/root/route" });
      expect(link).toMatchObject({
        href: "http://localhost:3000/root/route",
        basePath: "/",
      });
    });

    it("Does not link to the dev host in production", () => {
      env.NODE_ENV = "production";

      const link = resolveZone({ config, basePath, href: "/root/route" });
      expect(link).toMatchObject({
        href: "/root/route",
        basePath: "/",
      });
    });
  });
});
