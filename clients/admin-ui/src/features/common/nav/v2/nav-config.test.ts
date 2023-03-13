import { describe, expect, it } from "@jest/globals";

import { ScopeRegistryEnum } from "~/types/api";

import {
  canAccessRoute,
  configureNavGroups,
  findActiveNav,
  NAV_CONFIG,
} from "./nav-config";

const ALL_SCOPES = [
  ScopeRegistryEnum.PRIVACY_REQUEST_READ,
  ScopeRegistryEnum.CONNECTION_CREATE_OR_UPDATE,
  ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE,
  ScopeRegistryEnum.DATAMAP_READ,
  ScopeRegistryEnum.CLI_OBJECTS_READ,
  ScopeRegistryEnum.CLI_OBJECTS_CREATE,
  ScopeRegistryEnum.CLI_OBJECTS_UPDATE,
  ScopeRegistryEnum.USER_READ,
];

describe("configureNavGroups", () => {
  it("includes all navigation groups for users with all scopes", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      userScopes: ALL_SCOPES,
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

    // NOTE: the data map should _not_ include the Plus routes (/datamap, /classify-systems, etc.)
    expect(navGroups[2]).toMatchObject({
      title: "Data map",
      children: [
        { title: "View systems", path: "/system" },
        { title: "Add systems", path: "/add-systems" },
        { title: "Manage datasets", path: "/dataset" },
      ],
    });

    expect(navGroups[3]).toMatchObject({
      title: "Management",
      children: [
        { title: "Taxonomy", path: "/taxonomy" },
        { title: "Users", path: "/user-management" },
        { title: "About Fides", path: "/management/about" },
      ],
    });
  });

  it("includes the Plus routes when running with Fidesplus API", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      hasPlus: true,
      userScopes: ALL_SCOPES,
    });

    expect(navGroups[0]).toMatchObject({
      title: "Home",
      children: [{ title: "Home", path: "/" }],
    });

    // The data map _should_ include the actual "/datamap".
    expect(navGroups[2]).toMatchObject({
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

  // TODO: tests temporarily disabled due to https://github.com/ethyca/fides/issues/2769
  describe.skip("configure by scopes", () => {
    it("does not render paths the user does not have scopes for", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: [ScopeRegistryEnum.SYSTEM_READ],
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
        userScopes: [ScopeRegistryEnum.DATABASE_RESET],
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
        userScopes: [ScopeRegistryEnum.PRIVACY_REQUEST_READ],
      });
      expect(navGroups[1]).toMatchObject({
        title: "Privacy requests",
        children: [{ title: "Request manager", path: "/privacy-requests" }],
      });
    });

    it("does not show /datamap if plus is not enabled but user has the scope", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: ALL_SCOPES,
      });

      expect(navGroups[0]).toMatchObject({
        title: "Home",
        children: [{ title: "Home", path: "/" }],
      });

      // The data map should _not_ include the actual "/datamap".
      expect(navGroups[2]).toMatchObject({
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
    userScopes: ALL_SCOPES,
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

  // TODO: tests temporarily disabled due to https://github.com/ethyca/fides/issues/2769
  describe.skip("canAccessRoute", () => {
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
        userScopes: [ScopeRegistryEnum.SYSTEM_CREATE],
      },
      {
        path: "/privacy-requests",
        expected: false,
        userScopes: [ScopeRegistryEnum.SYSTEM_CREATE],
      },
      {
        path: "/privacy-requests",
        expected: true,
        userScopes: [ScopeRegistryEnum.PRIVACY_REQUEST_READ],
      },
      {
        path: "/privacy-requests?queryParam",
        expected: true,
        userScopes: [ScopeRegistryEnum.PRIVACY_REQUEST_READ],
      },
    ];
    accessTestCases.forEach(({ path, expected, userScopes }) => {
      it(`${path} is scope restricted`, () => {
        expect(canAccessRoute({ path, userScopes })).toBe(expected);
      });
    });
  });
});
