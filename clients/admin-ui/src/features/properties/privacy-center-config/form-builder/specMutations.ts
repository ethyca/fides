import type { ComponentType } from "./catalog";
import type { JsonRenderSpec } from "./mapper";

type EditableComponentType = Exclude<ComponentType, "Form">;

const DEFAULT_PROPS: Record<EditableComponentType, Record<string, unknown>> = {
  Text: { label: "New text field", required: false },
  Select: {
    label: "New select field",
    required: false,
    options: ["Option 1"],
  },
  MultiSelect: {
    label: "New multi-select field",
    required: false,
    options: ["Option 1"],
  },
  Location: { label: "Location", required: false },
};

const uniqueName = (
  spec: JsonRenderSpec,
  base: string,
): { name: string; elementId: string } => {
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
  return { name, elementId: `f_${name}` };
};

const baseFromType: Record<EditableComponentType, string> = {
  Text: "text_field",
  Select: "select_field",
  MultiSelect: "multi_select_field",
  Location: "location_field",
};

export const emptySpec = (): JsonRenderSpec => ({
  root: "form",
  elements: {
    form: { type: "Form", props: {}, children: [] },
  },
});

export const addField = (
  spec: JsonRenderSpec | null,
  type: EditableComponentType,
): { spec: JsonRenderSpec; elementId: string } => {
  const current = spec ?? emptySpec();
  const root = current.elements[current.root];
  const { name, elementId } = uniqueName(current, baseFromType[type]);

  const next: JsonRenderSpec = {
    ...current,
    elements: {
      ...current.elements,
      [elementId]: {
        type,
        props: { name, ...DEFAULT_PROPS[type] },
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
