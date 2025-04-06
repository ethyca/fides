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
  ScopeRegistryEnum.PROPERTY_READ,
  ScopeRegistryEnum.FIDES_CLOUD_CONFIG_READ,
  ScopeRegistryEnum.CONFIG_READ,
  ScopeRegistryEnum.CONFIG_UPDATE,
  ScopeRegistryEnum.CUSTOM_ASSET_UPDATE,
  ScopeRegistryEnum.DATA_USE_READ,
  ScopeRegistryEnum.DATA_CATEGORY_READ,
  ScopeRegistryEnum.DATA_SUBJECT_READ,
];

describe("configureNavGroups", () => {
  it("includes all navigation groups for users with all scopes", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      userScopes: ALL_SCOPES,
    });

    expect(navGroups[0]).toMatchObject({
      title: "Overview",
      children: [{ title: "Home", path: "/" }],
    });

    // NOTE: the data map should _not_ include the Plus routes (/plus/datamap, /classify-systems, etc.)
    expect(navGroups[1]).toMatchObject({
      title: "Data inventory",
      children: [
        { title: "System inventory", path: routes.SYSTEM_ROUTE },
        { title: "Add systems", path: routes.ADD_SYSTEMS_ROUTE },
        { title: "Manage datasets", path: routes.DATASET_ROUTE },
      ],
    });

    expect(navGroups[2]).toMatchObject({
      title: "Privacy requests",
      children: [
        { title: "Request manager", path: routes.PRIVACY_REQUESTS_ROUTE },
        {
          title: "Connection manager",
          path: routes.DATASTORE_CONNECTION_ROUTE,
        },
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
      title: "Overview",
      children: [{ title: "Home", path: "/" }],
    });

    // The data map _should_ include the actual "/plus/datamap".
    expect(navGroups[1]).toMatchObject({
      title: "Data inventory",
      children: [
        { title: "Data lineage", path: routes.DATAMAP_ROUTE },
        { title: "System inventory", path: routes.SYSTEM_ROUTE },
        { title: "Add systems", path: routes.ADD_SYSTEMS_ROUTE },
        { title: "Manage datasets", path: routes.DATASET_ROUTE },
        { title: "Reporting", path: routes.REPORTING_DATAMAP_ROUTE },
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
        title: "Overview",
        children: [{ title: "Home", path: "/" }],
      });

      expect(navGroups[1]).toMatchObject({
        title: "Data inventory",
        children: [{ title: "System inventory", path: routes.SYSTEM_ROUTE }],
      });
    });

    it("only shows minimal nav when user has the wrong scopes", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        // entirely irrelevant scope in this case
        userScopes: [ScopeRegistryEnum.DATABASE_RESET],
      });

      expect(navGroups[0]).toMatchObject({
        title: "Overview",
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
        title: "Overview",
        children: [{ title: "Home", path: "/" }],
      });

      // The data map should _not_ include the actual "/plus/datamap".
      expect(navGroups[1]).toMatchObject({
        title: "Data inventory",
        children: [
          { title: "System inventory", path: routes.SYSTEM_ROUTE },
          { title: "Add systems", path: routes.ADD_SYSTEMS_ROUTE },
          { title: "Manage datasets", path: routes.DATASET_ROUTE },
        ],
      });
    });
  });

  describe("fides cloud", () => {
    it("shows domain verification page when fides cloud is enabled", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: ALL_SCOPES,
        flags: undefined,
        hasPlus: true,
        hasFidesCloud: true,
      });

      expect(
        navGroups[4].children
          .map((c) => c.title)
          .find((title) => title === "Domain verification"),
      ).toEqual("Domain verification");
    });

    it("does not show domain verification page when fides cloud is disabled", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: ALL_SCOPES,
        flags: undefined,
        hasPlus: true,
        hasFidesCloud: false,
      });

      expect(
        navGroups[4].children
          .map((c) => c.title)
          .find((title) => title === "Domain verification"),
      ).toEqual(undefined);
    });
  });

  describe("fides plus", () => {
    it("shows domain management when plus and scopes are enabled", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: [
          ScopeRegistryEnum.CONFIG_READ,
          ScopeRegistryEnum.CONFIG_UPDATE,
        ],
        flags: undefined,
        hasPlus: true,
        hasFidesCloud: false,
      });

      expect(
        navGroups[1].children
          .map((c) => ({ title: c.title, path: c.path }))
          .find((c) => c.title === "Domains"),
      ).toEqual({
        title: "Domains",
        path: routes.DOMAIN_MANAGEMENT_ROUTE,
      });
    });

    it("hide domain management when plus is disabled", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: [
          ScopeRegistryEnum.CONFIG_READ,
          ScopeRegistryEnum.CONFIG_UPDATE,
          // include this so Management group is non-empty without domains
          ScopeRegistryEnum.USER_READ,
        ],
        flags: undefined,
        hasPlus: false,
        hasFidesCloud: false,
      });

      expect(
        navGroups[1].children
          .map((c) => ({ title: c.title, path: c.path }))
          .find((c) => c.title === "Domains"),
      ).toEqual(undefined);
    });

    it("hide domain management when scopes are wrong", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: [
          ScopeRegistryEnum.ALLOW_LIST_CREATE,
          ScopeRegistryEnum.ALLOW_LIST_UPDATE,
        ],
        flags: undefined,
        hasPlus: true,
        hasFidesCloud: false,
      });

      expect(
        navGroups[1]?.children
          .map((c) => ({ title: c.title, path: c.path }))
          .find((c) => c.title === "Domains"),
      ).toEqual(undefined);
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
        title: "Settings",
        children: [
          { title: "Users", path: routes.USER_MANAGEMENT_ROUTE },
          { title: "Taxonomy", path: routes.TAXONOMY_ROUTE },
          { title: "Email templates", path: routes.EMAIL_TEMPLATES_ROUTE },
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
        title: "Settings",
        children: [
          { title: "Users", path: routes.USER_MANAGEMENT_ROUTE },
          { title: "Organization", path: routes.ORGANIZATION_MANAGEMENT_ROUTE },
          { title: "Taxonomy", path: routes.TAXONOMY_ROUTE },
          {
            title: "Email templates",
            path: routes.EMAIL_TEMPLATES_ROUTE,
          },
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
        title: "Overview",
        path: "/",
      },
    },
    {
      path: routes.SYSTEM_ROUTE,
      expected: {
        title: "Data inventory",
        path: routes.SYSTEM_ROUTE,
      },
    },
    {
      path: routes.DATAMAP_ROUTE,
      expected: {
        title: "Data inventory",
        path: routes.DATAMAP_ROUTE,
      },
    },
    {
      path: routes.ADD_SYSTEMS_ROUTE,
      expected: {
        title: "Data inventory",
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
    {
      path: routes.PRIVACY_EXPERIENCE_ROUTE,
      expected: {
        title: "Consent",
        path: routes.PRIVACY_EXPERIENCE_ROUTE,
      },
    },
    {
      path: routes.PRIVACY_NOTICES_ROUTE,
      expected: {
        title: "Consent",
        path: routes.PRIVACY_NOTICES_ROUTE,
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
