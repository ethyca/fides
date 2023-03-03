import { describe, expect, it } from "@jest/globals";

import { ScopeRegistry } from "~/types/api";

import {
  canAccessRoute,
  configureNavGroups,
  findActiveNav,
  NAV_CONFIG,
} from "./nav-config";

describe("configureNavGroups", () => {
  it("only includes home and management by default", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      userScopes: [],
    });

    expect(navGroups[0]).toMatchObject({
      title: "Home",
      children: [{ title: "Home", path: "/" }],
    });

    expect(navGroups[1]).toMatchObject({
      title: "Management",
      children: [{ title: "About Fides", path: "/management/about" }],
    });
  });

  it("includes the privacy requests group when there are connections", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      hasConnections: true,
      userScopes: [
        ScopeRegistry.PRIVACY_REQUEST_READ,
        ScopeRegistry.CONNECTION_CREATE_OR_UPDATE,
      ],
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
      userScopes: [
        ScopeRegistry.CLI_OBJECTS_CREATE,
        ScopeRegistry.CLI_OBJECTS_READ,
      ],
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
      userScopes: [
        ScopeRegistry.DATAMAP_READ,
        ScopeRegistry.CLI_OBJECTS_CREATE,
        ScopeRegistry.CLI_OBJECTS_READ,
        ScopeRegistry.CLI_OBJECTS_UPDATE,
      ],
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
  describe("configure by scopes", () => {
    it("does not render paths the user does not have scopes for", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        hasSystems: true,
        userScopes: [ScopeRegistry.CLI_OBJECTS_READ],
      });

      expect(navGroups[0]).toMatchObject({
        title: "Home",
        children: [{ title: "Home", path: "/" }],
      });

      expect(navGroups[1]).toMatchObject({
        title: "Data map",
        children: [{ title: "View systems", path: "/system" }],
      });
    });

    it("only shows minimal nav when user has the wrong scopes", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        // entirely irrelevant scope in this case
        userScopes: [ScopeRegistry.DATABASE_RESET],
      });

      expect(navGroups[0]).toMatchObject({
        title: "Home",
        children: [{ title: "Home", path: "/" }],
      });

      expect(navGroups[1]).toMatchObject({
        title: "Management",
        children: [{ title: "About Fides", path: "/management/about" }],
      });
    });

    it("conditionally shows request manager using scopes", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        hasSystems: true,
        hasConnections: true,
        userScopes: [ScopeRegistry.PRIVACY_REQUEST_READ],
      });
      expect(navGroups[1]).toMatchObject({
        title: "Privacy requests",
        children: [{ title: "Request manager", path: "/privacy-requests" }],
      });
    });

    it("does not show /datamap if plus is not enabled but user has the scope", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        hasSystems: true,
        userScopes: [
          ScopeRegistry.DATAMAP_READ,
          ScopeRegistry.CLI_OBJECTS_CREATE,
          ScopeRegistry.CLI_OBJECTS_READ,
        ],
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
  });
});

describe("findActiveNav", () => {
  const navGroups = configureNavGroups({
    config: NAV_CONFIG,
    hasPlus: true,
    hasSystems: true,
    hasConnections: true,
    userScopes: [
      ScopeRegistry.DATAMAP_READ,
      ScopeRegistry.CLI_OBJECTS_CREATE,
      ScopeRegistry.CLI_OBJECTS_READ,
      ScopeRegistry.CONNECTION_CREATE_OR_UPDATE,
    ],
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

  describe("canAccessRoute", () => {
    const accessTestCases = [
      {
        path: "/",
        expected: true,
        userScopes: [],
      },
      {
        path: "/add-systems",
        expected: false,
        userScopes: [],
      },
      {
        path: "/add-systems",
        expected: true,
        userScopes: [ScopeRegistry.CLI_OBJECTS_CREATE],
      },
      {
        path: "/privacy-requests",
        expected: false,
        userScopes: [ScopeRegistry.CLI_OBJECTS_CREATE],
      },
      {
        path: "/privacy-requests",
        expected: true,
        userScopes: [ScopeRegistry.PRIVACY_REQUEST_READ],
      },
      {
        path: "/privacy-requests?queryParam",
        expected: true,
        userScopes: [ScopeRegistry.PRIVACY_REQUEST_READ],
      },
    ];
    accessTestCases.forEach(({ path, expected, userScopes }) => {
      it(`${path} is scope restricted`, () => {
        expect(canAccessRoute({ path, userScopes })).toBe(expected);
      });
    });
  });
});
