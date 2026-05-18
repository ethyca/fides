import type {
  JsonRenderSpec,
  PcCustomField,
  PcCustomFields,
  PcLocationField,
  PcMultiSelectField,
  PcRadioField,
  PcSelectField,
  PcTextField,
} from "./types";

const COMPONENT_FOR_FIELD: Record<PcCustomField["field_type"], string> = {
  text: "Text",
  select: "Select",
  multiselect: "MultiSelect",
  radio: "Radio",
  location: "Location",
};

const IDENTITY_COMPONENT_FOR_KEY: Record<string, string> = {
  email: "Email",
  name: "Name",
  phone: "Phone",
};

const visibilityToJsonRender = (
  conditions: NonNullable<PcCustomField["visible_when"]>,
): unknown[] =>
  conditions.map((c) => {
    const entry: Record<string, unknown> = {
      $state: `/form/${c.source_field}`,
    };
    if (c.operator === "set" || c.operator === "empty") {
      entry[c.operator] = true;
    } else {
      entry[c.operator] = c.value;
    }
    return entry;
  });

const buildIdentityElement = (
  identityKey: string,
  mode: "required" | "optional",
): JsonRenderSpec["elements"][string] => ({
  type: IDENTITY_COMPONENT_FOR_KEY[identityKey],
  props: { required: mode === "required" },
  children: [],
});

const buildCustomElement = (
  name: string,
  field: PcCustomField,
): JsonRenderSpec["elements"][string] => {
  const componentType = COMPONENT_FOR_FIELD[field.field_type];
  const props: Record<string, unknown> = {
    name,
    label: field.label,
    required: field.required ?? false,
  };
  if (field.placeholder !== undefined) {
    props.placeholder = field.placeholder;
  }

  switch (field.field_type) {
    case "text": {
      const text = field as PcTextField;
      if (text.default_value !== undefined && text.default_value !== null) {
        props.default_value = text.default_value;
      }
      if (text.hidden !== undefined) {
        props.hidden = text.hidden;
      }
      if (text.query_param_key !== undefined && text.query_param_key !== null) {
        props.query_param_key = text.query_param_key;
      }
      break;
    }
    case "select": {
      const sel = field as PcSelectField;
      props.options = sel.options;
      if (sel.default_value !== undefined && sel.default_value !== null) {
        props.default_value = sel.default_value;
      }
      break;
    }
    case "radio": {
      const rad = field as PcRadioField;
      props.options = rad.options;
      if (rad.default_value !== undefined && rad.default_value !== null) {
        props.default_value = rad.default_value;
      }
      break;
    }
    case "multiselect": {
      const ms = field as PcMultiSelectField;
      props.options = ms.options;
      if (ms.default_value !== undefined && ms.default_value !== null) {
        props.default_value = ms.default_value;
      }
      break;
    }
    case "location": {
      const loc = field as PcLocationField;
      if (loc.options !== undefined) {
        props.options = loc.options;
      }
      if (loc.ip_geolocation_hint !== undefined) {
        props.ip_geolocation_hint = loc.ip_geolocation_hint;
      }
      break;
    }
    default: {
      const exhaustive: never = field;
      throw new Error(
        `Unhandled field type: ${(exhaustive as PcCustomField).field_type}`,
      );
    }
  }

  const element: JsonRenderSpec["elements"][string] = {
    type: componentType,
    props,
    children: [],
  };
  if (field.visible_when && field.visible_when.length > 0) {
    (element as { visible?: unknown }).visible = visibilityToJsonRender(
      field.visible_when,
    );
  }
  return element;
};

export function pcShapeToJsonSpec(
  pcShape: PcCustomFields,
  identityInputs?: Record<string, "required" | "optional"> | null,
  fieldOrder?: string[] | null,
): JsonRenderSpec {
  const elements: JsonRenderSpec["elements"] = {
    form: { type: "Form", props: {}, children: [] },
  };
  const childIds: string[] = [];
  const seenKeys = new Set<string>();

  // When fieldOrder is provided, render keys in that exact sequence so identity
  // and custom fields can interleave freely. Any keys configured but missing
  // from fieldOrder fall through to the legacy ordering at the end (so a
  // hand-edited YAML adding a field without updating field_order still shows it).
  if (fieldOrder && fieldOrder.length > 0) {
    fieldOrder.forEach((key) => {
      if (seenKeys.has(key)) {
        return;
      }
      const elementId = `f_${key}`;
      if (key in IDENTITY_COMPONENT_FOR_KEY) {
        const mode = identityInputs?.[key];
        if (mode !== "required" && mode !== "optional") {
          return;
        }
        elements[elementId] = buildIdentityElement(key, mode);
        childIds.push(elementId);
        seenKeys.add(key);
        return;
      }
      const customField = pcShape[key];
      if (customField) {
        elements[elementId] = buildCustomElement(key, customField);
        childIds.push(elementId);
        seenKeys.add(key);
      }
      // Unknown key (neither identity nor custom): skipped silently. Backend
      // validation rejects this case at save time; we don't crash on stale data.
    });
  }

  // Legacy default order for keys not covered by fieldOrder: identity first
  // (name → email → phone), then customs in pcShape iteration order.
  if (identityInputs) {
    (["name", "email", "phone"] as const).forEach((key) => {
      if (seenKeys.has(key)) {
        return;
      }
      const mode = identityInputs[key];
      if (mode === "required" || mode === "optional") {
        const elementId = `f_${key}`;
        elements[elementId] = buildIdentityElement(key, mode);
        childIds.push(elementId);
        seenKeys.add(key);
      }
    });
  }

  Object.entries(pcShape).forEach(([name, field]) => {
    if (seenKeys.has(name)) {
      return;
    }
    const elementId = `f_${name}`;
    elements[elementId] = buildCustomElement(name, field);
    childIds.push(elementId);
    seenKeys.add(name);
  });

  elements.form.children = childIds;
  return { root: "form", elements };
}
