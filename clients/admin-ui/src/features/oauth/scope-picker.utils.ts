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
