import { describe, expect, it } from "@jest/globals";

import { ScopeRegistryEnum } from "~/types/api";

import { MODULE_CARD_ITEMS } from "./constants";
import { configureTiles } from "./tile-config";

const ALL_SCOPES_FOR_TILES = [
  ScopeRegistryEnum.DATAMAP_READ,
  ScopeRegistryEnum.PRIVACY_REQUEST_REVIEW,
  ScopeRegistryEnum.CONNECTION_CREATE_OR_UPDATE,
  ScopeRegistryEnum.SYSTEM_READ,
  ScopeRegistryEnum.SYSTEM_CREATE,
];

describe("configureTiles", () => {
  it("does not return view datamap if not plus", () => {
    const tiles = configureTiles({
      config: MODULE_CARD_ITEMS,
      hasPlus: false,
      userScopes: ALL_SCOPES_FOR_TILES,
      flags: {},
    });

    expect(tiles.filter((t) => t.href === "/datamap").length).toEqual(0);
  });

  it("includes datamap view if plus", () => {
    const tiles = configureTiles({
      config: MODULE_CARD_ITEMS,
      hasPlus: true,
      userScopes: ALL_SCOPES_FOR_TILES,
      flags: {},
    });
    expect(tiles.filter((t) => t.href === "/datamap").length).toEqual(1);
  });

  describe("configure by scopes", () => {
    it("returns no tiles if user has no scopes", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        userScopes: [],
        flags: {},
      });

      expect(tiles.length).toEqual(0);
    });

    it("returns no tiles if user has wrong scopes", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        // irrelevant scope
        userScopes: [ScopeRegistryEnum.DATABASE_RESET],
        flags: {},
      });
      expect(tiles.length).toEqual(0);
    });

    it("conditionally shows add systems based on scope", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        userScopes: [ScopeRegistryEnum.SYSTEM_CREATE],
        flags: {},
      });
      expect(tiles.map((t) => t.name)).toEqual(["Add systems"]);
    });

    it("conditionally shows view datamap", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        hasPlus: true,
        userScopes: [ScopeRegistryEnum.DATAMAP_READ],
        flags: {},
      });
      expect(tiles.map((t) => t.name)).toEqual(["View data map"]);
    });

    it("conditionally shows reviewing privacy requests", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        userScopes: [ScopeRegistryEnum.PRIVACY_REQUEST_REVIEW],
        flags: {},
      });
      expect(tiles.map((t) => t.name)).toEqual(["Review privacy requests"]);
    });

    it("can combine scopes to show multiple tiles", () => {
      const tiles = configureTiles({
        config: MODULE_CARD_ITEMS,
        userScopes: [
          ScopeRegistryEnum.PRIVACY_REQUEST_REVIEW,
          ScopeRegistryEnum.CONNECTION_CREATE_OR_UPDATE,
        ],
        flags: {},
      });
      expect(tiles.map((t) => t.name)).toEqual(["Review privacy requests"]);
    });
  });
});
