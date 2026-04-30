import type { JsonRenderSpec, PcCustomFields } from "./mapper";
import { mapSpecToPcShape } from "./mapper";

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

/**
 * Returns true if mapping the rich json-render spec to a PC shape
 * yields anything other than the saved PC shape — including any
 * mapping errors, which we treat as drift.
 */
export function detectDrift(
  richSpec: JsonRenderSpec,
  savedPcShape: PcCustomFields,
): boolean {
  const { pcShape, errors } = mapSpecToPcShape(richSpec);
  if (errors.length > 0) {
    return true;
  }
  return stableJson(pcShape) !== stableJson(savedPcShape);
}
