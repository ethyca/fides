export const stableJson = (value: unknown): string => {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return JSON.stringify(value);
  }
  const obj = value as Record<string, unknown>;
  const sortedKeys = Object.keys(obj).sort();
  const parts = sortedKeys.map(
    (key) => `${JSON.stringify(key)}:${stableJson(obj[key])}`,
  );
  return `{${parts.join(",")}}`;
};
