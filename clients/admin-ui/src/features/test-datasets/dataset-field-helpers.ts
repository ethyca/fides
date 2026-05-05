import { DatasetField } from "~/types/api";

/** Walk nested fields to find and update the one at fieldPath */
export const updateFieldAtPath = (
  fields: DatasetField[],
  segments: string[],
  updates: Partial<DatasetField>,
): DatasetField[] =>
  fields.map((f) => {
    if (f.name !== segments[0]) {
      return f;
    }
    if (segments.length === 1) {
      return { ...f, ...updates };
    }
    return {
      ...f,
      fields: updateFieldAtPath(f.fields ?? [], segments.slice(1), updates),
    };
  });

/** Get the children fields of a field at the given path */
export const getFieldsAtPath = (
  fields: DatasetField[],
  segments: string[],
): DatasetField[] => {
  const match = fields.find((f) => f.name === segments[0]);
  if (!match) {
    return [];
  }
  if (segments.length === 1) {
    return match.fields ?? [];
  }
  return getFieldsAtPath(match.fields ?? [], segments.slice(1));
};

/** Append a new child field to the parent at the given path */
export const addNestedField = (
  fields: DatasetField[],
  segments: string[],
  newField: DatasetField,
): DatasetField[] =>
  fields.map((f) => {
    if (f.name !== segments[0]) {
      return f;
    }
    if (segments.length === 1) {
      return { ...f, fields: [...(f.fields ?? []), newField] };
    }
    return {
      ...f,
      fields: addNestedField(f.fields ?? [], segments.slice(1), newField),
    };
  });

/** Recursively remove a field at the given path */
export const removeFieldAtPath = (
  fields: DatasetField[],
  segments: string[],
): DatasetField[] => {
  if (segments.length === 1) {
    return fields.filter((f) => f.name !== segments[0]);
  }
  return fields.map((f) => {
    if (f.name !== segments[0]) {
      return f;
    }
    return {
      ...f,
      fields: removeFieldAtPath(f.fields ?? [], segments.slice(1)),
    };
  });
};
