import { describe, expect, it } from "@jest/globals";

import { ScopeRegistry } from "~/types/api";

import { MODULE_CARD_ITEMS } from "./constants";
import { configureTiles } from "./tile-config";

const ALL_SCOPES_FOR_TILES = [
  ScopeRegistry.DATAMAP_READ,
  ScopeRegistry.PRIVACY_REQUEST_CREATE,
  ScopeRegistry.CONNECTION_CREATE_OR_UPDATE,
  ScopeRegistry.CLI_OBJECTS_READ,
  ScopeRegistry.CLI_OBJECTS_CREATE,
];

describe("configureTiles", () => {
  it("does not return view datamap if not plus", () => {
    const tiles = configureTiles({
      config: MODULE_CARD_ITEMS,
      hasPlus: false,
      hasSystems: true,
      userScopes: ALL_SCOPES_FOR_TILES,
    });

    expect(tiles.filter((t) => t.href === "/datamap").length).toEqual(0);
  });

  it("includes datamap view if plus", () => {
    const tiles = configureTiles({
      config: MODULE_CARD_ITEMS,
      hasPlus: true,
      hasSystems: true,
      userScopes: ALL_SCOPES_FOR_TILES,
    });
    expect(tiles.filter((t) => t.href === "/datamap").length).toEqual(1);
  });

  it("can exclude tiles that require systems or connectors", () => {
    const tiles = configureTiles({
      config: MODULE_CARD_ITEMS,
      hasPlus: true,
      hasSystems: false,
      hasConnections: false,
      userScopes: ALL_SCOPES_FOR_TILES,
    });
    expect(tiles.map((t) => t.name)).toEqual([
      "Add systems",
      "Configure privacy requests",
    ]);
  });

  it("can include tiles that require systems", () => {
    const tiles = configureTiles({
      config: MODULE_CARD_ITEMS,
      hasPlus: true,
      hasSystems: true,
      userScopes: ALL_SCOPES_FOR_TILES,
    });
    expect(tiles.map((t) => t.name)).toEqual([
      "View data map",
      "Add systems",
      "View systems",
      "Configure privacy requests",
    ]);
  });

  it("can include tiles that require connectors", () => {
    const tiles = configureTiles({
      config: MODULE_CARD_ITEMS,
      hasConnections: true,
      userScopes: ALL_SCOPES_FOR_TILES,
    });
    expect(tiles.map((t) => t.name)).toEqual([
      "Add systems",
      "Configure privacy requests",
      "Review privacy requests",
    ]);
  });

  describe("configure by scopes", () => {
    it("returns no tiles if user has no scopes", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        userScopes: [],
      });

      expect(tiles.length).toEqual(0);
    });

    it("returns no tiles if user has wrong scopes", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        // irrelevant scope
        userScopes: [ScopeRegistry.DATABASE_RESET],
      });
      expect(tiles.length).toEqual(0);
    });

    it("conditionally shows add systems based on scope", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        userScopes: [ScopeRegistry.CLI_OBJECTS_CREATE],
      });
      expect(tiles.map((t) => t.name)).toEqual(["Add systems"]);
    });

    it("conditionally shows configure privacy requests", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        userScopes: [ScopeRegistry.CONNECTION_CREATE_OR_UPDATE],
      });
      expect(tiles.map((t) => t.name)).toEqual(["Configure privacy requests"]);
    });

    it("conditionally shows view datamap", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        hasPlus: true,
        hasSystems: true,
        userScopes: [ScopeRegistry.DATAMAP_READ],
      });
      expect(tiles.map((t) => t.name)).toEqual(["View data map"]);
    });

    it("conditionally shows reviewing privacy requests", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        hasConnections: true,
        userScopes: [ScopeRegistry.PRIVACY_REQUEST_CREATE],
      });
      expect(tiles.map((t) => t.name)).toEqual(["Review privacy requests"]);
    });

    it("can combine scopes to show multiple tiles", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        hasConnections: true,
        userScopes: [
          ScopeRegistry.PRIVACY_REQUEST_CREATE,
          ScopeRegistry.CONNECTION_CREATE_OR_UPDATE,
        ],
      });
      expect(tiles.map((t) => t.name)).toEqual([
        "Configure privacy requests",
        "Review privacy requests",
      ]);
    });
  });
});
