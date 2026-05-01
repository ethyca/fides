import type {
  JsonRenderSpec,
  PcCustomField,
  PcCustomFields,
  PcLocationField,
  PcMultiSelectField,
  PcSelectField,
  PcTextField,
} from "./mapper";

const COMPONENT_FOR_FIELD: Record<PcCustomField["field_type"], string> = {
  text: "Text",
  select: "Select",
  multiselect: "MultiSelect",
  location: "Location",
};

export function synthesizeSpecFromPcShape(
  pcShape: PcCustomFields,
): JsonRenderSpec {
  const elements: JsonRenderSpec["elements"] = {
    form: { type: "Form", props: {}, children: [] },
  };

  const childIds: string[] = [];
  for (const [name, field] of Object.entries(pcShape)) {
    const elementId = `f_${name}`;
    childIds.push(elementId);

    const componentType = COMPONENT_FOR_FIELD[field.field_type];
    const props: Record<string, unknown> = {
      name,
      label: field.label,
      required: field.required ?? false,
    };

    switch (field.field_type) {
      case "text": {
        const text = field as PcTextField;
        if (text.default_value !== undefined && text.default_value !== null) {
          props.default_value = text.default_value;
        }
        if (text.hidden !== undefined) {
          props.hidden = text.hidden;
        }
        if (
          text.query_param_key !== undefined &&
          text.query_param_key !== null
        ) {
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
        const _exhaustive: never = field;
        throw new Error(
          `Unhandled field type: ${(_exhaustive as PcCustomField).field_type}`,
        );
      }
    }

    elements[elementId] = {
      type: componentType,
      props,
      children: [],
    };
  }
  elements.form.children = childIds;

  return { root: "form", elements };
}
