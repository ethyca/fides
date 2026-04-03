import {
  formatResourceLabel,
  groupScopesByResource,
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

