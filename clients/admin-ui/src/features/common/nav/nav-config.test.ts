import { describe, expect, it } from "@jest/globals";

import { ScopeRegistryEnum } from "~/types/api";

import {
  configureNavGroups,
  findActiveNav,
  NAV_CONFIG,
  NavGroup,
} from "./nav-config";
import * as routes from "./routes";

const ALL_SCOPES = Object.values(ScopeRegistryEnum);

/**
 * Find a nav group by title, asserting that it exists.
 * Gives clear failure messages instead of cryptic optional-chaining errors.
 */
const findGroup = (navGroups: NavGroup[], title: string): NavGroup => {
  const group = navGroups.find((g) => g.title === title);
  expect(group).toBeDefined();
  return group!;
};

describe("configureNavGroups", () => {
  it("includes all navigation groups for users with all scopes", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      userScopes: ALL_SCOPES,
    });

    expect(findGroup(navGroups, "Overview").children).toMatchObject([
      { title: "Home", path: "/" },
    ]);

    // NOTE: the data map should _not_ include the Plus routes (/plus/datamap, /classify-systems, etc.)
    expect(findGroup(navGroups, "Data inventory").children).toMatchObject([
      { title: "System inventory", path: routes.SYSTEM_ROUTE },
      { title: "Add systems", path: routes.ADD_SYSTEMS_ROUTE },
      { title: "Manage datasets", path: routes.DATASET_ROUTE },
    ]);

    expect(findGroup(navGroups, "Privacy requests").children).toMatchObject([
      { title: "Request manager", path: routes.PRIVACY_REQUESTS_ROUTE },
    ]);
  });

  it("includes the Plus routes when running with Fidesplus API", () => {
    const navGroups = configureNavGroups({
      config: NAV_CONFIG,
      hasPlus: true,
      userScopes: ALL_SCOPES,
    });

    expect(findGroup(navGroups, "Overview").children).toMatchObject([
      { title: "Home", path: "/" },
    ]);

    // The data map _should_ include the actual "/plus/datamap".
    expect(findGroup(navGroups, "Data inventory").children).toMatchObject([
      { title: "Data lineage", path: routes.DATAMAP_ROUTE },
      { title: "System inventory", path: routes.SYSTEM_ROUTE },
      { title: "Add systems", path: routes.ADD_SYSTEMS_ROUTE },
      { title: "Manage datasets", path: routes.DATASET_ROUTE },
      { title: "Data map report", path: routes.REPORTING_DATAMAP_ROUTE },
      { title: "Asset report", path: routes.REPORTING_ASSETS_ROUTE },
    ]);
  });

  describe("configure by scopes", () => {
    it("does not render paths the user does not have scopes for", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: [ScopeRegistryEnum.SYSTEM_READ],
      });

      expect(findGroup(navGroups, "Overview").children).toMatchObject([
        { title: "Home", path: "/" },
      ]);

      expect(findGroup(navGroups, "Data inventory").children).toMatchObject([
        { title: "System inventory", path: routes.SYSTEM_ROUTE },
      ]);
    });

    it("only shows minimal nav when user has the wrong scopes", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        // entirely irrelevant scope in this case
        userScopes: [ScopeRegistryEnum.DATABASE_RESET],
      });

      expect(findGroup(navGroups, "Overview").children).toMatchObject([
        { title: "Home", path: "/" },
      ]);

      // Data inventory should not exist when user has irrelevant scopes
      const dataInventoryGroup = navGroups.find(
        (g) => g.title === "Data inventory",
      );
      expect(dataInventoryGroup).toBeUndefined();
    });

    it("conditionally shows request manager using scopes", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: [ScopeRegistryEnum.PRIVACY_REQUEST_READ],
      });
      expect(findGroup(navGroups, "Privacy requests").children).toMatchObject([
        { title: "Request manager", path: routes.PRIVACY_REQUESTS_ROUTE },
      ]);
    });

    it("does not show /plus/datamap if plus is not enabled but user has the scope", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: ALL_SCOPES,
      });

      expect(findGroup(navGroups, "Overview").children).toMatchObject([
        { title: "Home", path: "/" },
      ]);

      // The data map should _not_ include the actual "/plus/datamap".
      expect(findGroup(navGroups, "Data inventory").children).toMatchObject([
        { title: "System inventory", path: routes.SYSTEM_ROUTE },
        { title: "Add systems", path: routes.ADD_SYSTEMS_ROUTE },
        { title: "Manage datasets", path: routes.DATASET_ROUTE },
      ]);
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
        findGroup(navGroups, "Settings")
          .children.map((c) => c.title)
          .find((title) => title === "Domain verification"),
      ).toBeDefined();
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
        findGroup(navGroups, "Settings")
          .children.map((c) => c.title)
          .find((title) => title === "Domain verification"),
      ).toBeUndefined();
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
        findGroup(navGroups, "Settings")
          .children.map((c) => ({ title: c.title, path: c.path }))
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
        findGroup(navGroups, "Settings")
          .children.map((c) => ({ title: c.title, path: c.path }))
          .find((c) => c.title === "Domains"),
      ).toBeUndefined();
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
        findGroup(navGroups, "Settings")
          .children.map((c) => ({ title: c.title, path: c.path }))
          .find((c) => c.title === "Domains"),
      ).toBeUndefined();
    });
  });

  describe("configure by feature flags", () => {
    it("excludes feature flagged routes when disabled", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: ALL_SCOPES,
        flags: undefined,
        hasPlus: true,
      });

      expect(
        findGroup(navGroups, "Detection & Discovery").children,
      ).toMatchObject([
        { title: "Action center", path: routes.ACTION_CENTER_ROUTE },
      ]);
    });

    it("includes feature flagged routes when enabled", () => {
      const navGroups = configureNavGroups({
        config: NAV_CONFIG,
        userScopes: ALL_SCOPES,
        flags: {
          dataCatalog: true,
        },
        hasPlus: true,
      });

      expect(
        findGroup(navGroups, "Detection & Discovery").children,
      ).toMatchObject([
        { title: "Action center", path: routes.ACTION_CENTER_ROUTE },
        { title: "Data catalog", path: routes.DATA_CATALOG_ROUTE },
      ]);
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
