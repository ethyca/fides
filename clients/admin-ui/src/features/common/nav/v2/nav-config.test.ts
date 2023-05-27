import { describe, expect, it } from "@jest/globals";

import { ScopeRegistryEnum } from "~/types/api";

import { configureNavGroups, findActiveNav, NAV_CONFIG } from "./nav-config";
import * as routes from "./routes";

const ALL_SCOPES = [
  ScopeRegistryEnum.PRIVACY_REQUEST_READ,
  ScopeRegistryEnum.CONNECTION_CREATE_OR_UPDATE,
  ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE,
  ScopeRegistryEnum.DATAMAP_READ,
  ScopeRegistryEnum.SYSTEM_CREATE,
  ScopeRegistryEnum.SYSTEM_READ,
  ScopeRegistryEnum.SYSTEM_UPDATE,
  ScopeRegistryEnum.CTL_DATASET_CREATE,
  ScopeRegistryEnum.USER_UPDATE,
  ScopeRegistryEnum.USER_READ,
  ScopeRegistryEnum.DATA_CATEGORY_CREATE,
  ScopeRegistryEnum.ORGANIZATION_READ,
  ScopeRegistryEnum.ORGANIZATION_UPDATE,
  ScopeRegistryEnum.PRIVACY_NOTICE_READ,
  ScopeRegistryEnum.PRIVACY_EXPERIENCE_READ,
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
        { title: "Request manager", path: routes.PRIVACY_REQUESTS_ROUTE },
        {
          title: "Connection manager",
          path: routes.DATASTORE_CONNECTION_ROUTE,
        },
      ],
    });

    // NOTE: the data map should _not_ include the Plus routes (/plus/datamap, /classify-systems, etc.)
    expect(navGroups[2]).toMatchObject({
      title: "Data map",
      children: [
        { title: "View systems", path: routes.SYSTEM_ROUTE },
        { title: "Add systems", path: routes.ADD_SYSTEMS_ROUTE },
        { title: "Manage datasets", path: routes.DATASET_ROUTE },
      ],
    });

    expect(navGroups[3]).toMatchObject({
      title: "Management",
      children: [
        { title: "Users", path: routes.USER_MANAGEMENT_ROUTE },
        { title: "Taxonomy", path: routes.TAXONOMY_ROUTE },
        { title: "About Fides", path: routes.ABOUT_ROUTE },
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

    // The data map _should_ include the actual "/plus/datamap".
    expect(navGroups[2]).toMatchObject({
      title: "Data map",
      children: [
        { title: "View map", path: routes.DATAMAP_ROUTE },
        { title: "View systems", path: routes.SYSTEM_ROUTE },
        { title: "Add systems", path: routes.ADD_SYSTEMS_ROUTE },
        { title: "Manage datasets", path: routes.DATASET_ROUTE },
        { title: "Classify systems", path: routes.CLASSIFY_SYSTEMS_ROUTE },
      ],
    });
  });

  describe("configure by scopes", () => {
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
        children: [{ title: "View systems", path: routes.SYSTEM_ROUTE }],
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
    });

    it("conditionally shows request manager using scopes", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: [ScopeRegistryEnum.PRIVACY_REQUEST_READ],
      });
      expect(navGroups[1]).toMatchObject({
        title: "Privacy requests",
        children: [
          { title: "Request manager", path: routes.PRIVACY_REQUESTS_ROUTE },
        ],
      });
    });

    it("does not show /plus/datamap if plus is not enabled but user has the scope", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: ALL_SCOPES,
      });

      expect(navGroups[0]).toMatchObject({
        title: "Home",
        children: [{ title: "Home", path: "/" }],
      });

      // The data map should _not_ include the actual "/plus/datamap".
      expect(navGroups[2]).toMatchObject({
        title: "Data map",
        children: [
          { title: "View systems", path: routes.SYSTEM_ROUTE },
          { title: "Add systems", path: routes.ADD_SYSTEMS_ROUTE },
          { title: "Manage datasets", path: routes.DATASET_ROUTE },
        ],
      });
    });
  });

  describe("configure by feature flags", () => {
    it("excludes feature flagged routes when disabled", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: ALL_SCOPES,
        flags: undefined,
      });

      expect(navGroups[3]).toMatchObject({
        title: "Management",
        children: [
          { title: "Users", path: routes.USER_MANAGEMENT_ROUTE },
          { title: "Taxonomy", path: routes.TAXONOMY_ROUTE },
          { title: "About Fides", path: routes.ABOUT_ROUTE },
        ],
      });
    });

    it("includes feature flagged routes when enabled", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: ALL_SCOPES,
        flags: {
          organizationManagement: true,
        },
      });

      expect(navGroups[3]).toMatchObject({
        title: "Management",
        children: [
          { title: "Users", path: routes.USER_MANAGEMENT_ROUTE },
          { title: "Organization", path: routes.ORGANIZATION_MANAGEMENT_ROUTE },
          { title: "Taxonomy", path: routes.TAXONOMY_ROUTE },
          { title: "About Fides", path: routes.ABOUT_ROUTE },
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
    flags: { privacyNotices: true, privacyExperience: true },
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
      path: routes.SYSTEM_ROUTE,
      expected: {
        title: "Data map",
        path: routes.SYSTEM_ROUTE,
      },
    },
    {
      path: routes.DATAMAP_ROUTE,
      expected: {
        title: "Data map",
        path: routes.DATAMAP_ROUTE,
      },
    },
    {
      path: routes.ADD_SYSTEMS_ROUTE,
      expected: {
        title: "Data map",
        path: routes.ADD_SYSTEMS_ROUTE,
      },
    },
    // Inexact match is the default.
    {
      path: `${routes.DATASTORE_CONNECTION_ROUTE}/new`,
      expected: {
        title: "Privacy requests",
        path: routes.DATASTORE_CONNECTION_ROUTE,
      },
    },
    // Nested side nav child
    {
      path: routes.PRIVACY_EXPERIENCE_ROUTE,
      expected: {
        title: "Privacy requests",
        // this _might_ not be the right thing to expect, but it at least works intuitively
        // since then both the Consent route and the Privacy experience route will be marked as "active"
        // since they both start with "/consent". if we see weird behavior with which nav is active
        // we may need to revisit the logic in `findActiveNav`
        path: routes.CONSENT_ROUTE,
      },
    },
    // Parent side nav
    {
      path: routes.CONSENT_ROUTE,
      expected: {
        title: "Privacy requests",
        path: routes.CONSENT_ROUTE,
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
