import { describe, expect, it } from "@jest/globals";

import {
  filterAndRankNavItems,
  FlatNavItem,
  matchesNavQuery,
  navMatchRank,
} from "./useNavSearchItems";

const makeItem = (overrides: Partial<FlatNavItem> = {}): FlatNavItem => ({
  title: "Request manager",
  path: "/privacy-requests",
  groupTitle: "Privacy requests",
  ...overrides,
});

describe("matchesNavQuery", () => {
  it("returns true for an empty or whitespace query", () => {
    const item = makeItem();
    expect(matchesNavQuery(item, "")).toBe(true);
    expect(matchesNavQuery(item, "   ")).toBe(true);
  });

  it("matches against the item's title (case-insensitive)", () => {
    const item = makeItem();
    expect(matchesNavQuery(item, "request")).toBe(true);
    expect(matchesNavQuery(item, "REQUEST")).toBe(true);
    expect(matchesNavQuery(item, "MaNaGeR")).toBe(true);
  });

  it("matches against the group title", () => {
    // Motivating example: searching "privacy requests" should surface
    // Request manager via its group title, even though the title alone
    // doesn't contain that phrase.
    const item = makeItem();
    expect(matchesNavQuery(item, "privacy requests")).toBe(true);
  });

  it("matches against the parent title for tab-like items", () => {
    const item = makeItem({
      title: "Manual tasks",
      parentTitle: "Request manager",
    });
    expect(matchesNavQuery(item, "request manager")).toBe(true);
  });

  it("matches against hand-curated keywords", () => {
    const item = makeItem({ keywords: ["DSR", "data subject"] });
    expect(matchesNavQuery(item, "dsr")).toBe(true);
    expect(matchesNavQuery(item, "data subject")).toBe(true);
  });

  it("returns false when the query matches none of the fields", () => {
    const item = makeItem({ keywords: ["DSR"] });
    expect(matchesNavQuery(item, "integrations")).toBe(false);
  });

  it("tolerates items without optional parent/keyword fields", () => {
    const item = makeItem();
    expect(matchesNavQuery(item, "privacy")).toBe(true);
    expect(matchesNavQuery(item, "nonsense")).toBe(false);
  });
});

describe("navMatchRank", () => {
  it("ranks title matches above parent, group, and keyword matches", () => {
    const titleHit = makeItem({ title: "Privacy requests" });
    const parentHit = makeItem({
      title: "Manual tasks",
      parentTitle: "Privacy requests",
    });
    const groupHit = makeItem({
      title: "Pre-approval webhooks",
      groupTitle: "Privacy requests",
    });
    const keywordHit = makeItem({
      title: "Request manager",
      groupTitle: "Other group",
      keywords: ["privacy requests"],
    });

    expect(navMatchRank(titleHit, "privacy requests")).toBe(0);
    expect(navMatchRank(parentHit, "privacy requests")).toBe(1);
    expect(navMatchRank(groupHit, "privacy requests")).toBe(2);
    expect(navMatchRank(keywordHit, "privacy requests")).toBe(3);
  });

  it("returns Infinity when no field matches", () => {
    const item = makeItem({ keywords: ["dsr"] });
    expect(navMatchRank(item, "integrations")).toBe(Number.POSITIVE_INFINITY);
  });
});

describe("filterAndRankNavItems", () => {
  it("places direct title matches before indirect (parent/group/keyword) matches", () => {
    const settingsPrivacyRequests = makeItem({
      title: "Privacy requests",
      path: "/settings/privacy-requests",
      groupTitle: "Settings",
    });
    const requestManager = makeItem({
      title: "Request manager",
      path: "/privacy-requests",
      groupTitle: "Privacy requests",
    });
    const dsrPolicies = makeItem({
      title: "DSR policies",
      path: "/dsr-policies",
      groupTitle: "Privacy requests",
    });

    // Source order: indirect matches come first; ranking should bubble the
    // direct title match to the front.
    const ranked = filterAndRankNavItems(
      [requestManager, dsrPolicies, settingsPrivacyRequests],
      "privacy requests",
    );

    expect(ranked.map((i) => i.path)).toEqual([
      "/settings/privacy-requests", // title match (rank 0)
      "/privacy-requests", // group match (rank 2), preserves source order
      "/dsr-policies", // group match (rank 2)
    ]);
  });

  it("filters out items that don't match", () => {
    const a = makeItem({ title: "Integrations", groupTitle: "Core" });
    const b = makeItem({ title: "Request manager", groupTitle: "Core" });
    expect(
      filterAndRankNavItems([a, b], "request").map((i) => i.title),
    ).toEqual(["Request manager"]);
  });

  it("preserves source order within a single rank tier", () => {
    const first = makeItem({ title: "Request manager", path: "/a" });
    const second = makeItem({ title: "Request log", path: "/b" });
    expect(
      filterAndRankNavItems([first, second], "request").map((i) => i.path),
    ).toEqual(["/a", "/b"]);
  });
});
