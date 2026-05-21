import { useEffect, useMemo, useRef, useState } from "react";

import { resolveApplicableFields } from "~/lib/condition-evaluator";
import { setsEqual } from "~/lib/set-utils";
import type { Condition, CustomConfigField } from "~/types/config";

/**
 * Extracts the set of field keys that are referenced by any display_condition
 * across the given field definitions.
 */
const extractWatchedKeys = (
  fields: Record<string, CustomConfigField>,
): Set<string> => {
  const watched = new Set<string>();

  const walk = (condition: Condition): void => {
    if ("field_address" in condition) {
      watched.add(condition.field_address);
    }
    if ("conditions" in condition) {
      condition.conditions.forEach(walk);
    }
  };

  Object.values(fields).forEach((field) => {
    if (field.display_condition) {
      walk(field.display_condition);
    }
  });

  return watched;
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
): { applicableFields: Set<string>; conditionError: boolean } => {
  const prevResult = useRef<Set<string>>(new Set());
  const [conditionError, setConditionError] = useState(false);
  const errorRef = useRef(false);

  const watchedKeys = useMemo(
    () => extractWatchedKeys(customFields),
    [customFields],
  );

  // Snapshot only the watched values into a stable string for memoization.
  // Safe to stringify because formValues are string | string[] (no circular refs).
  const watchedSnapshot = useMemo(() => {
    if (watchedKeys.size === 0) {
      return "";
    }
    const entries: [string, unknown][] = [];
    watchedKeys.forEach((key) => {
      entries.push([key, formValues[key] ?? null]);
    });
    entries.sort(([a], [b]) => a.localeCompare(b));
    return JSON.stringify(entries);
  }, [watchedKeys, formValues]);

  const applicableFields = useMemo(() => {
    try {
      const result = resolveApplicableFields(customFields, formValues);
      errorRef.current = false;
      // Return the same reference if the set hasn't changed
      if (setsEqual(result, prevResult.current)) {
        return prevResult.current;
      }
      prevResult.current = result;
      return result;
    } catch {
      errorRef.current = true;
      return prevResult.current;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customFields, watchedSnapshot]);

  // Sync the error ref to state in an effect to avoid setState during render
  useEffect(() => {
    setConditionError(errorRef.current);
  }, [applicableFields]);

  return { applicableFields, conditionError };
};
