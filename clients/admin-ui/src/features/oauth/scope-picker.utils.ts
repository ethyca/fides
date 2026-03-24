export interface ScopeTreeNode {
  key: string;
  title: string;
  children?: ScopeTreeNode[];
}

/**
 * Groups an array of `resource:action` scope strings by their resource prefix.
 *
 * Example:
 *   groupScopesByResource(["client:create", "client:read", "user:create"])
 *   // => { client: ["client:create", "client:read"], user: ["user:create"] }
 */
export function groupScopesByResource(
  scopes: string[],
): Record<string, string[]> {
  return scopes.reduce<Record<string, string[]>>((acc, scope) => {
    const resource = scope.split(":")[0];
    if (!acc[resource]) {
      acc[resource] = [];
    }
    acc[resource].push(scope);
    return acc;
  }, {});
}

/**
 * Converts a resource key like "custom_field" or "cli-objects" into a
 * human-readable label like "Custom Field" or "Cli Objects".
 */
export function formatResourceLabel(resource: string): string {
  return resource
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

/**
 * Converts a flat list of `resource:action` scope strings into a tree of
 * DataNode objects suitable for Ant Design's Tree (and Tree Transfer).
 *
 * Each resource becomes a parent node whose `key` is the resource name.
 * Each action becomes a child node whose `key` is the full scope string.
 *
 * Example:
 *   scopesToTreeData(["client:create", "client:read"])
 *   // => [{ key: "client", title: "Client", children: [
 *   //      { key: "client:create", title: "create" },
 *   //      { key: "client:read",   title: "read"   },
 *   //    ]}]
 */
export function scopesToTreeData(scopes: string[]): ScopeTreeNode[] {
  const grouped = groupScopesByResource(scopes);
  return Object.keys(grouped)
    .sort()
    .map((resource) => ({
      key: resource,
      title: formatResourceLabel(resource),
      children: grouped[resource].map((scope) => ({
        key: scope,
        title: scope.split(":")[1],
      })),
    }));
}

/**
 * Given a list of checked keys (which may include parent resource keys),
 * returns only the leaf scope strings (those containing ":").
 * Parent keys are checked by Ant Design Tree for UI state but are not
 * themselves valid scope values.
 */
export function leafScopesFromKeys(keys: string[]): string[] {
  return keys.filter((k) => k.includes(":"));
}
