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

// Keys whose value is functionally absent when set to a backend default.
// The Pydantic schema serializes these on every field whether or not they
// were explicitly set, so the mapper's omit-when-unset output won't
// stable-JSON-match the persisted shape unless we strip them first.
const BACKEND_DEFAULT_VALUES: Record<string, unknown> = {
  hidden: false,
  required: true,
  default_value: null,
  query_param_key: null,
  options: null,
  ip_geolocation_hint: false,
  placeholder: null,
  visible_when: null,
};

const stripBackendDefaults = (
  field: Record<string, unknown>,
): Record<string, unknown> => {
  const result: Record<string, unknown> = {};
  Object.entries(field).forEach(([key, value]) => {
    if (
      key in BACKEND_DEFAULT_VALUES &&
      BACKEND_DEFAULT_VALUES[key] === value
    ) {
      return;
    }
    result[key] = value;
  });
  return result;
};

const normalizeShape = (shape: PcCustomFields): Record<string, unknown> => {
  const out: Record<string, unknown> = {};
  Object.entries(shape).forEach(([name, field]) => {
    out[name] = stripBackendDefaults(field as unknown as Record<string, unknown>);
  });
  return out;
};

/**
 * Returns true if mapping the rich json-render spec to a PC shape
 * yields anything other than the saved PC shape — including any
 * mapping errors, which we treat as drift. Backend-default keys
 * (e.g. `hidden: false`, `required: true`) are normalized out before
 * comparison so a clean save → reload round-trip doesn't surface as
 * drift just because the backend echoed unset fields.
 */
export function detectDrift(
  richSpec: JsonRenderSpec,
  savedPcShape: PcCustomFields,
): boolean {
  const { pcShape, errors } = mapSpecToPcShape(richSpec);
  if (errors.length > 0) {
    return true;
  }
  return (
    stableJson(normalizeShape(pcShape)) !==
    stableJson(normalizeShape(savedPcShape))
  );
}
