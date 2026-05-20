import { CustomConfigField, VisibilityCondition } from "~/types/config";

const isEmpty = (v: unknown) =>
  v === undefined ||
  v === null ||
  v === "" ||
  (Array.isArray(v) && v.length === 0);

const evalCondition = (
  condition: VisibilityCondition,
  values: Record<string, unknown>,
): boolean => {
  const sourceValue = values[condition.source_field];
  switch (condition.operator) {
    case "set":
      return !isEmpty(sourceValue);
    case "empty":
      return isEmpty(sourceValue);
    case "eq":
      return String(sourceValue ?? "") === String(condition.value ?? "");
    case "ne":
      return String(sourceValue ?? "") !== String(condition.value ?? "");
    case "contains":
      if (Array.isArray(sourceValue)) {
        return sourceValue.includes(condition.value as never);
      }
      return String(sourceValue ?? "").includes(String(condition.value ?? ""));
    default:
      return true;
  }
};

/**
 * Evaluate a field's `visible_when` conditions against a values map.
 * Returns true when the field should render (no conditions, or every
 * condition passes — AND semantics).
 */
export const isFieldVisible = (
  field: Pick<CustomConfigField, "visible_when">,
  values: Record<string, unknown>,
): boolean => {
  if (!field.visible_when || field.visible_when.length === 0) {
    return true;
  }
  return field.visible_when.every((c) => evalCondition(c, values));
};
