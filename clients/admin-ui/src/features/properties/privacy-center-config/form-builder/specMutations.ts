import type { ComponentType } from "./catalog";
import type { JsonRenderSpec } from "./types";

type EditableComponentType = Exclude<ComponentType, "Form">;

// Defaults excluding name/label — those are derived from the type so that
// snakeCase(label) === name, which lets the FieldPropertiesPanel auto-sync
// the name from the label until the user explicitly customizes the name.
const DEFAULT_PROPS: Record<EditableComponentType, Record<string, unknown>> = {
  Text: { required: false },
  Select: { required: false, options: ["Option 1"] },
  MultiSelect: { required: false, options: ["Option 1"] },
  Radio: { required: false, options: ["Option 1", "Option 2"] },
  Location: { required: false },
  Email: { required: false },
  Name: { required: false },
  Phone: { required: false },
};

// Identity field types use fixed element IDs and have no configurable name/label.
const IDENTITY_ELEMENT_IDS: Partial<Record<EditableComponentType, string>> = {
  Email: "f_email",
  Name: "f_name",
  Phone: "f_phone",
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
  Radio: { base: "radio_field", label: "Radio field" },
  Location: { base: "location_field", label: "Location field" },
  Email: { base: "email", label: "Email" },
  Name: { base: "name", label: "Name" },
  Phone: { base: "phone", label: "Phone" },
};

export const emptySpec = (): JsonRenderSpec => ({
  root: "form",
  elements: {
    form: { type: "Form", props: {}, children: [] },
  },
});

/**
 * Seed used when a form-builder page loads for an action that has no saved
 * fields yet. Defaults to a required Email identity field.
 */
export const defaultSpec = (): JsonRenderSpec => ({
  root: "form",
  elements: {
    form: {
      type: "Form",
      props: {},
      children: ["f_email"],
    },
    f_email: {
      type: "Email",
      props: { required: true },
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

  // Identity types use a fixed element ID and props without name/label.
  const identityId = IDENTITY_ELEMENT_IDS[type];
  if (identityId) {
    if (current.elements[identityId]) {
      return { spec: current, elementId: identityId };
    }
    return {
      spec: {
        ...current,
        elements: {
          ...current.elements,
          [identityId]: { type, props: { required: false }, children: [] },
          [current.root]: {
            ...root,
            children: [...root.children, identityId],
          },
        },
      },
      elementId: identityId,
    };
  }

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

/**
 * Set or clear the `visible` condition on an element. Pass `undefined` to
 * remove the condition entirely (the field becomes always-visible).
 */
export const setFieldVisibility = (
  spec: JsonRenderSpec,
  elementId: string,
  visible: unknown | undefined,
): JsonRenderSpec => {
  const target = spec.elements[elementId];
  if (!target) {
    return spec;
  }
  const next = { ...target } as JsonRenderSpec["elements"][string] & {
    visible?: unknown;
  };
  if (visible === undefined) {
    delete next.visible;
  } else {
    next.visible = visible;
  }
  return {
    ...spec,
    elements: {
      ...spec.elements,
      [elementId]: next,
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
