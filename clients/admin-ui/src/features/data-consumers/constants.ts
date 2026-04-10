export const formatScopeKeyLabel = (key: string): string =>
  key.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());

export const DATA_CONSUMER_FORM_ID = "data-consumer-form";

/**
 * Pick the best display value from a scope object.
 * If a display_key is provided (from ConsumerTypeDescriptor), use it.
 * Otherwise falls back to joining all scope values.
 */
export const getDisplayNameForScope = (
  scope: Record<string, string>,
  displayKey?: string,
): string => {
  if (displayKey && scope[displayKey]) {
    return scope[displayKey];
  }
  return Object.values(scope).join(", ");
};
