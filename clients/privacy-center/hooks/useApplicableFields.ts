import { useMemo, useRef } from "react";

import { resolveApplicableFields } from "~/lib/condition-evaluator";
import type { CustomConfigField } from "~/types/config";

/**
 * Extracts the set of field keys that are referenced by any display_condition
 * across the given field definitions.
 */
const extractWatchedKeys = (
  fields: Record<string, CustomConfigField>,
): Set<string> => {
  const watched = new Set<string>();

  const walk = (condition: unknown): void => {
    if (!condition || typeof condition !== "object") {
      return;
    }
    if ("field_address" in (condition as Record<string, unknown>)) {
      watched.add((condition as { field_address: string }).field_address);
    }
    if ("conditions" in (condition as Record<string, unknown>)) {
      const group = condition as { conditions: unknown[] };
      group.conditions.forEach(walk);
    }
  };

  Object.values(fields).forEach((field) => {
    if (field.display_condition) {
      walk(field.display_condition);
    }
  });

  return watched;
};

const setsEqual = (a: Set<string>, b: Set<string>): boolean => {
  if (a.size !== b.size) {
    return false;
  }
  let equal = true;
  a.forEach((item) => {
    if (!b.has(item)) {
      equal = false;
    }
  });
  return equal;
};

/**
 * React hook that resolves which custom fields are currently applicable
 * based on form values and display_condition rules.
 *
 * Returns a stable Set<string> of applicable field keys — the same reference
 * is returned when the result hasn't changed.
 */
export const useApplicableFields = (
  customFields: Record<string, CustomConfigField>,
  formValues: Record<string, string | string[]>,
): Set<string> => {
  const prevResult = useRef<Set<string>>(new Set());

  const watchedKeys = useMemo(
    () => extractWatchedKeys(customFields),
    [customFields],
  );

  // Snapshot only the watched values into a stable string for memoization
  const watchedSnapshot = useMemo(() => {
    if (watchedKeys.size === 0) {
      return "";
    }
    const entries: string[] = [];
    watchedKeys.forEach((key) => {
      const val = formValues[key];
      entries.push(
        `${key}=${Array.isArray(val) ? val.join(",") : (val ?? "")}`,
      );
    });
    return entries.sort().join("|");
  }, [watchedKeys, formValues]);

  return useMemo(() => {
    const result = resolveApplicableFields(customFields, formValues);
    // Return the same reference if the set hasn't changed
    if (setsEqual(result, prevResult.current)) {
      return prevResult.current;
    }
    prevResult.current = result;
    return result;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customFields, watchedSnapshot]);
};
