import type { ComponentType } from "./catalog";
import type { JsonRenderSpec } from "./mapper";

type EditableComponentType = Exclude<ComponentType, "Form">;

// Defaults excluding name/label — those are derived from the type so that
// snakeCase(label) === name, which lets the FieldPropertiesPanel auto-sync
// the name from the label until the user explicitly customizes the name.
const DEFAULT_PROPS: Record<EditableComponentType, Record<string, unknown>> = {
  Text: { required: false },
  Select: { required: false, options: ["Option 1"] },
  MultiSelect: { required: false, options: ["Option 1"] },
  Location: { required: false },
};

const uniqueName = (
  spec: JsonRenderSpec,
  base: string,
): { suffix: number; name: string; elementId: string } => {
  const usedNames = new Set<string>();
  Object.values(spec.elements).forEach((el) => {
    const candidate = (el.props as { name?: unknown } | undefined)?.name;
    if (typeof candidate === "string") {
      usedNames.add(candidate);
    }
  });
  let suffix = 1;
  let name = `${base}_${suffix}`;
  while (usedNames.has(name) || spec.elements[`f_${name}`]) {
    suffix += 1;
    name = `${base}_${suffix}`;
  }
  return { suffix, name, elementId: `f_${name}` };
};

interface TypeDefaults {
  base: string;
  label: string;
}

// Pairs name-base + label-base such that snakeCase(label) === name. The
// matching `_${suffix}` / ` ${suffix}` is appended to both at add time.
const TYPE_DEFAULTS: Record<EditableComponentType, TypeDefaults> = {
  Text: { base: "text_field", label: "Text field" },
  Select: { base: "select_field", label: "Select field" },
  MultiSelect: { base: "multi_select_field", label: "Multi select field" },
  Location: { base: "location_field", label: "Location field" },
};

export const emptySpec = (): JsonRenderSpec => ({
  root: "form",
  elements: {
    form: { type: "Form", props: {}, children: [] },
  },
});

/**
 * Seed used when a form-builder page loads for an action that has no saved
 * fields yet. Mirrors the historical Fides privacy-center config defaults
 * (first_name + last_name) plus a hidden tenant_id field for multi-tenant
 * routing via URL query param.
 */
export const defaultSpec = (): JsonRenderSpec => ({
  root: "form",
  elements: {
    form: {
      type: "Form",
      props: {},
      children: ["f_first_name", "f_last_name", "f_tenant_id"],
    },
    f_first_name: {
      type: "Text",
      props: { name: "first_name", label: "First name", required: true },
      children: [],
    },
    f_last_name: {
      type: "Text",
      props: { name: "last_name", label: "Last name", required: false },
      children: [],
    },
    f_tenant_id: {
      type: "Text",
      props: {
        name: "tenant_id",
        label: "Tenant ID",
        required: false,
        hidden: true,
        query_param_key: "tenant_id",
      },
      children: [],
    },
  },
});

export const addField = (
  spec: JsonRenderSpec | null,
  type: EditableComponentType,
): { spec: JsonRenderSpec; elementId: string } => {
  const current = spec ?? emptySpec();
  const root = current.elements[current.root];
  const defaults = TYPE_DEFAULTS[type];
  const { suffix, name, elementId } = uniqueName(current, defaults.base);
  const label = `${defaults.label} ${suffix}`;

  const next: JsonRenderSpec = {
    ...current,
    elements: {
      ...current.elements,
      [elementId]: {
        type,
        props: { name, label, ...DEFAULT_PROPS[type] },
        children: [],
      },
      [current.root]: {
        ...root,
        children: [...root.children, elementId],
      },
    },
  };
  return { spec: next, elementId };
};

export const updateField = (
  spec: JsonRenderSpec,
  elementId: string,
  props: Record<string, unknown>,
): JsonRenderSpec => {
  const target = spec.elements[elementId];
  if (!target) {
    return spec;
  }
  return {
    ...spec,
    elements: {
      ...spec.elements,
      [elementId]: { ...target, props },
    },
  };
};

export const removeField = (
  spec: JsonRenderSpec,
  elementId: string,
): JsonRenderSpec => {
  const root = spec.elements[spec.root];
  if (!root || !spec.elements[elementId]) {
    return spec;
  }
  const remaining = { ...spec.elements };
  delete remaining[elementId];
  return {
    ...spec,
    elements: {
      ...remaining,
      [spec.root]: {
        ...root,
        children: root.children.filter((id) => id !== elementId),
      },
    },
  };
};

export const reorderFields = (
  spec: JsonRenderSpec,
  newOrder: string[],
): JsonRenderSpec => {
  const root = spec.elements[spec.root];
  if (!root) {
    return spec;
  }
  return {
    ...spec,
    elements: {
      ...spec.elements,
      [spec.root]: { ...root, children: newOrder },
    },
  };
};
