import type { Condition, ConditionGroup, ConditionLeaf } from "~/types/config";

import { setsEqual } from "./set-utils";

/**
 * Check whether a value should be considered "present" for exists/not_exists.
 * Empty strings and empty arrays are treated as absent, matching backend behavior.
 */
const hasValue = (val: unknown): boolean => {
  if (val === null || val === undefined) {
    return false;
  }
  if (val === "") {
    return false;
  }
  if (Array.isArray(val) && val.length === 0) {
    return false;
  }
  return true;
};

type ConditionValue = ConditionLeaf["value"];

const applyOperator = (
  operator: string,
  actual: unknown,
  expected: ConditionValue,
): boolean => {
  switch (operator) {
    case "eq":
      // Both null-ish values are considered equal
      if (!hasValue(actual) && !hasValue(expected)) {
        return true;
      }
      return actual === expected;

    case "neq":
      if (!hasValue(actual) && !hasValue(expected)) {
        return false;
      }
      return actual !== expected;

    case "exists":
      return hasValue(actual);

    case "not_exists":
      return !hasValue(actual);

    case "list_contains": {
      // data is array, check if it contains the expected value
      if (Array.isArray(actual)) {
        return actual.includes(expected);
      }
      // expected is array, check if it contains the actual value
      if (Array.isArray(expected)) {
        return expected.includes(actual as string | number | boolean);
      }
      return false;
    }

    default:
      return false;
  }
};

/**
 * Evaluate a single condition (leaf or group) against a flat data record.
 * Returns false on any error, matching backend behavior (conservative: field hidden).
 */
export const evaluateCondition = (
  condition: Condition,
  data: Record<string, unknown>,
): boolean => {
  try {
    if ("field_address" in condition) {
      // ConditionLeaf
      const leaf = condition as ConditionLeaf;
      const actual = data[leaf.field_address];
      return applyOperator(leaf.operator, actual, leaf.value);
    }
    // ConditionGroup
    const group = condition as ConditionGroup;
    const results = group.conditions.map((c) => evaluateCondition(c, data));
    return group.logical_operator === "and"
      ? results.every(Boolean)
      : results.some(Boolean);
  } catch {
    return false;
  }
};

/**
 * Evaluate a single field's applicability given a data view.
 * Extracted to avoid the no-loop-func lint rule in resolveApplicableFields.
 */
const isFieldApplicable = (
  condition: Condition | null | undefined,
  dataView: Record<string, unknown>,
): boolean => {
  if (!condition) {
    return true;
  }
  try {
    return evaluateCondition(condition, dataView);
  } catch {
    return false;
  }
};

/**
 * Evaluate one iteration of the fixed-point loop: given the current applicable
 * set, build a data view and return the next applicable set.
 */
const evaluateFieldSet = <T extends { display_condition?: Condition | null }>(
  currentApplicable: Set<string>,
  fields: Record<string, T>,
  formValues: Record<string, unknown>,
): Set<string> => {
  const dataView: Record<string, unknown> = {};
  currentApplicable.forEach((key) => {
    dataView[key] = formValues[key];
  });

  const next = new Set<string>();
  currentApplicable.forEach((key) => {
    const field = fields[key];
    if (isFieldApplicable(field.display_condition, dataView)) {
      next.add(key);
    }
  });
  return next;
};

/**
 * Fixed-point iteration to resolve which fields are applicable given current
 * form values. Mirrors the backend's `_resolve_applicable` algorithm.
 *
 * The condition graph is guaranteed acyclic (validated at save time), so this
 * converges in at most N iterations where N = number of fields.
 */
export const resolveApplicableFields = <
  T extends { display_condition?: Condition | null },
>(
  fields: Record<string, T>,
  formValues: Record<string, unknown>,
): Set<string> => {
  const keys = Object.keys(fields);
  let applicable = new Set(keys);
  let previous: Set<string>;

  do {
    previous = applicable;
    applicable = evaluateFieldSet(previous, fields, formValues);
  } while (!setsEqual(applicable, previous));

  return applicable;
};
