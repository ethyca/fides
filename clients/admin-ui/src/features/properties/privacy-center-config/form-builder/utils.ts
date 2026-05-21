import { catalog } from "./catalog";
import type { JsonRenderSpec } from "./types";

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

// Strip ```json … ``` fences and return the first balanced {...} object
// the LLM wrote. Falls back to the original string if no braces are found.
export const extractJson = (raw: string): string => {
  let body = raw.trim();
  const fence = body.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?```$/);
  if (fence) {
    body = fence[1].trim();
  }

  const firstBrace = body.indexOf("{");
  if (firstBrace === -1) {
    return body;
  }

  let depth = 0;
  let inString = false;
  let escape = false;
  for (let i = firstBrace; i < body.length; i += 1) {
    const ch = body[i];
    if (escape) {
      escape = false;
    } else if (ch === "\\") {
      escape = true;
    } else if (ch === '"') {
      inString = !inString;
    } else if (!inString) {
      if (ch === "{") {
        depth += 1;
      } else if (ch === "}") {
        depth -= 1;
        if (depth === 0) {
          return body.slice(firstBrace, i + 1);
        }
      }
    }
  }
  return body.slice(firstBrace);
};

export const tryParseSpec = (raw: string): JsonRenderSpec | null => {
  try {
    return JSON.parse(extractJson(raw)) as JsonRenderSpec;
  } catch {
    return null;
  }
};

const KNOWN_TYPES = new Set(Object.keys(catalog.components));

/**
 * Defense-in-depth: strip elements whose `type` is not in the catalog before
 * rendering in the preview. The LLM could return arbitrary component types;
 * unknown types would be no-ops in json-render, but removing them explicitly
 * keeps the spec clean and avoids surprises.
 */
export const sanitizeSpec = (spec: JsonRenderSpec): JsonRenderSpec => {
  const root = spec.elements[spec.root];
  if (!root) {
    return spec;
  }
  const validChildren = root.children.filter((id) => {
    const el = spec.elements[id];
    return el && KNOWN_TYPES.has(el.type);
  });
  const cleanElements: JsonRenderSpec["elements"] = {
    [spec.root]: { ...root, children: validChildren },
  };
  validChildren.forEach((id) => {
    cleanElements[id] = spec.elements[id];
  });
  return { ...spec, elements: cleanElements };
};
