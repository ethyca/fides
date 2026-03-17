import {
  formatResourceLabel,
  groupScopesByResource,
  leafScopesFromKeys,
  scopesToTreeData,
} from "./scope-picker.utils";

describe("groupScopesByResource", () => {
  it("groups scopes by the resource prefix", () => {
    const scopes = ["client:create", "client:read", "user:create"];
    const result = groupScopesByResource(scopes);
    expect(result).toEqual({
      client: ["client:create", "client:read"],
      user: ["user:create"],
    });
  });

  it("returns an empty object for an empty list", () => {
    expect(groupScopesByResource([])).toEqual({});
  });

  it("handles a single scope", () => {
    expect(groupScopesByResource(["privacy_request:read"])).toEqual({
      privacy_request: ["privacy_request:read"],
    });
  });

  it("preserves all scopes under the same resource", () => {
    const scopes = [
      "connection:read",
      "connection:create_or_update",
      "connection:delete",
      "connection:authorize",
    ];
    const result = groupScopesByResource(scopes);
    expect(result.connection).toHaveLength(4);
    expect(result.connection).toContain("connection:authorize");
  });
});

describe("formatResourceLabel", () => {
  it("capitalizes and replaces underscores with spaces", () => {
    expect(formatResourceLabel("custom_field")).toBe("Custom Field");
  });

  it("capitalizes and replaces hyphens with spaces", () => {
    expect(formatResourceLabel("cli-objects")).toBe("Cli Objects");
  });

  it("handles a single word", () => {
    expect(formatResourceLabel("connection")).toBe("Connection");
  });

  it("handles multiple underscores", () => {
    expect(formatResourceLabel("custom_field_definition")).toBe(
      "Custom Field Definition",
    );
  });
});

describe("scopesToTreeData", () => {
  it("produces parent nodes keyed by resource and child nodes keyed by full scope", () => {
    const result = scopesToTreeData(["client:create", "client:read"]);
    expect(result).toHaveLength(1);
    expect(result[0].key).toBe("client");
    expect(result[0].title).toBe("Client");
    expect(result[0].children).toHaveLength(2);
    expect(result[0].children![0]).toMatchObject({
      key: "client:create",
      title: "create",
    });
  });

  it("sorts resources alphabetically", () => {
    const result = scopesToTreeData([
      "user:read",
      "client:create",
      "privacy_request:read",
    ]);
    expect(result.map((n) => n.key)).toEqual([
      "client",
      "privacy_request",
      "user",
    ]);
  });

  it("returns an empty array for no scopes", () => {
    expect(scopesToTreeData([])).toEqual([]);
  });
});

describe("leafScopesFromKeys", () => {
  it("keeps only keys that contain a colon (leaf scopes)", () => {
    const keys = ["client", "client:create", "client:read", "user"];
    expect(leafScopesFromKeys(keys)).toEqual(["client:create", "client:read"]);
  });

  it("returns empty when only parent keys are present", () => {
    expect(leafScopesFromKeys(["client", "user"])).toEqual([]);
  });

  it("returns all keys when all are leaf scopes", () => {
    const keys = ["client:create", "user:read"];
    expect(leafScopesFromKeys(keys)).toEqual(keys);
  });
});
