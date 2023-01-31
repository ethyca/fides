import { describe, expect, it } from "@jest/globals";

import { configureNavGroups, findActiveNav, NAV_CONFIG } from "./nav-config";

describe("configureNavGroups", () => {
  it("only includes home and management by default", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
    });

    expect(navGroups[0]).toMatchObject({
      title: "Home",
      children: [{ title: "Home", path: "/" }],
    });

    expect(navGroups[1]).toMatchObject({
      title: "Management",
      children: [
        { title: "Taxonomy", path: "/taxonomy" },
        { title: "Users", path: "/user-management" },
        { title: "About Fides", path: "/management/about" },
      ],
    });
  });

  it("includes the privacy requests group when there are connections", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      hasConnections: true,
    });

    expect(navGroups[0]).toMatchObject({
      title: "Home",
      children: [{ title: "Home", path: "/" }],
    });

    expect(navGroups[1]).toMatchObject({
      title: "Privacy requests",
      children: [
        { title: "Request manager", path: "/privacy-requests" },
        { title: "Connection manager", path: "/datastore-connection" },
      ],
    });
  });

  it("includes the data map group when there are systems", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      hasSystems: true,
    });

    expect(navGroups[0]).toMatchObject({
      title: "Home",
      children: [{ title: "Home", path: "/" }],
    });

    // The data map should _not_ include the actual "/datamap".
    expect(navGroups[1]).toMatchObject({
      title: "Data map",
      children: [
        { title: "View systems", path: "/system" },
        { title: "Add systems", path: "/add-systems" },
        { title: "Manage datasets", path: "/dataset" },
      ],
    });
  });

  it("includes the visual data map when there are systems for Fidesplus", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      hasSystems: true,

      hasPlus: true,
    });

    expect(navGroups[0]).toMatchObject({
      title: "Home",
      children: [{ title: "Home", path: "/" }],
    });

    // The data map _should_ include the actual "/datamap".
    expect(navGroups[1]).toMatchObject({
      title: "Data map",
      children: [
        { title: "View map", path: "/datamap" },
        { title: "View systems", path: "/system" },
        { title: "Add systems", path: "/add-systems" },
        { title: "Manage datasets", path: "/dataset" },
        { title: "Classify systems", path: "/classify-systems" },
      ],
    });
  });
});

describe("findActiveNav", () => {
  const navGroups = configureNavGroups({
    config: NAV_CONFIG,
    hasPlus: true,
    hasSystems: true,
    hasConnections: true,
  });

  const testCases = [
    // "Home" requires an exact match.
    {
      path: "/",
      expected: {
        title: "Home",
        path: "/",
      },
    },
    {
      path: "/system",
      expected: {
        title: "Data map",
        path: "/system",
      },
    },
    {
      path: "/datamap",
      expected: {
        title: "Data map",
        path: "/datamap",
      },
    },
    {
      path: "/add-systems",
      expected: {
        title: "Data map",
        path: "/add-systems",
      },
    },
    // Inexact match is the default.
    {
      path: "/datastore-connection/new",
      expected: {
        title: "Privacy requests",
        path: "/datastore-connection",
      },
    },
  ] as const;

  testCases.forEach(({ path, expected }) => {
    it(`matches ${path} to ${expected.title} at ${expected.path}`, () => {
      const activeNav = findActiveNav({ navGroups, path });

      expect(activeNav?.title).toEqual(expected.title);
      expect(activeNav?.path).toEqual(expected.path);
    });
  });
});
