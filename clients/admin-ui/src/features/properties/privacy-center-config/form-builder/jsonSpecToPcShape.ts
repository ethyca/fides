import { catalog, ComponentType } from "./catalog";
import type {
  DroppedFeature,
  JsonRenderSpec,
  MapResult,
  PcCustomField,
  PcCustomFields,
  PcFieldBase,
  PcFieldType,
  PcLocationField,
  PcMultiSelectField,
  PcRadioField,
  PcSelectField,
  PcTextField,
  ValidationError,
  VisibilityCondition,
  VisibilityOperator,
} from "./types";

export type {
  DroppedFeature,
  JsonRenderElement,
  JsonRenderSpec,
  MapResult,
  PcCustomField,
  PcCustomFields,
  PcFieldBase,
  PcFieldType,
  PcLocationField,
  PcMultiSelectField,
  PcRadioField,
  PcSelectField,
  PcTextField,
  ValidationError,
  VisibilityCondition,
  VisibilityOperator,
} from "./types";

const FIELD_TYPE: Record<
  Exclude<ComponentType, "Form" | "Email" | "Name" | "Phone">,
  PcFieldType
> = {
  Text: "text",
  Select: "select",
  MultiSelect: "multiselect",
  Radio: "radio",
  Location: "location",
};

// Maps identity ComponentType names to their identity_inputs key.
const IDENTITY_TYPE_KEY: Partial<Record<string, string>> = {
  Email: "email",
  Name: "name",
  Phone: "phone",
};

const VISIBILITY_OPERATORS: VisibilityOperator[] = [
  "eq",
  "ne",
  "set",
  "empty",
  "contains",
];

const FORM_STATE_PREFIX = "/form/";

/**
 * Translate one json-render `visible` entry (e.g. `{ $state: "/form/x", eq: "y" }`)
 * into the legacy `VisibilityCondition` shape PC consumes. Returns null when
 * the entry doesn't match the supported pattern — caller should treat that as
 * a dropped feature so the Save dialog can warn the author.
 */
const visibilityEntryToCondition = (
  entry: unknown,
): VisibilityCondition | null => {
  if (!entry || typeof entry !== "object") {
    return null;
  }
  const obj = entry as Record<string, unknown>;
  const path = typeof obj.$state === "string" ? obj.$state : "";
  if (!path.startsWith(FORM_STATE_PREFIX)) {
    return null;
  }
  const sourceField = path.slice(FORM_STATE_PREFIX.length);
  if (!sourceField) {
    return null;
  }
  const matchedOp = VISIBILITY_OPERATORS.find((op) => op in obj);
  if (!matchedOp) {
    return null;
  }
  if (matchedOp === "set" || matchedOp === "empty") {
    if (obj[matchedOp] !== true) {
      return null;
    }
    return { source_field: sourceField, operator: matchedOp };
  }
  const rawValue = obj[matchedOp];
  if (typeof rawValue !== "string" && typeof rawValue !== "number") {
    return null;
  }
  return {
    source_field: sourceField,
    operator: matchedOp,
    value: rawValue as string | number,
  };
};

const translateVisible = (
  visible: unknown,
): { conditions: VisibilityCondition[]; failed: boolean } => {
  if (!Array.isArray(visible) || visible.length === 0) {
    return { conditions: [], failed: false };
  }
  const conditions: VisibilityCondition[] = [];
  let failed = false;
  visible.forEach((entry) => {
    const cond = visibilityEntryToCondition(entry);
    if (cond) {
      conditions.push(cond);
    } else {
      failed = true;
    }
  });
  return { conditions, failed };
};

const hasExpression = (value: unknown): boolean => {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const obj = value as Record<string, unknown>;
  if (
    "$state" in obj ||
    "$cond" in obj ||
    "$template" in obj ||
    "$computed" in obj
  ) {
    return true;
  }
  return Object.values(obj).some(hasExpression);
};

export function jsonSpecToPcShape(spec: JsonRenderSpec): MapResult {
  const droppedFeatures: DroppedFeature[] = [];
  const errors: ValidationError[] = [];
  const pcShape: PcCustomFields = {};
  const identityInputs: Record<string, "required" | "optional"> = {};
  const fieldOrder: string[] = [];

  const root = spec.elements?.[spec.root];
  if (!root || root.type !== "Form") {
    errors.push({ kind: "missing_form_root", rootId: spec.root });
    return { pcShape, identityInputs, fieldOrder, droppedFeatures, errors };
  }

  const seenNames: Record<string, string[]> = {};

  root.children.forEach((childId) => {
    const child = spec.elements[childId];
    if (!child) {
      errors.push({
        kind: "child_not_found",
        elementId: childId,
        parentId: spec.root,
      });
      return;
    }

    const { conditions: translatedVisibility, failed: visibilityFailed } =
      translateVisible(child.visible);
    if (child.visible !== undefined && visibilityFailed) {
      droppedFeatures.push({ kind: "visible", elementId: childId });
    }
    if (child.watch !== undefined) {
      droppedFeatures.push({ kind: "watch", elementId: childId });
    }
    Object.entries(child.props ?? {}).forEach(([propPath, propValue]) => {
      if (hasExpression(propValue)) {
        droppedFeatures.push({
          kind: "expression",
          elementId: childId,
          path: propPath,
        });
      }
    });

    // Identity field types (Email/Name/Phone) map to identity_inputs, not pcShape.
    const identityKey = IDENTITY_TYPE_KEY[child.type];
    if (identityKey !== undefined) {
      const validation = catalog.components[
        child.type as keyof typeof catalog.components
      ].props.safeParse(child.props);
      if (!validation.success) {
        errors.push({
          kind: "invalid_props",
          elementId: childId,
          message: validation.error.issues
            .map((i) => `${i.path.join(".")}: ${i.message}`)
            .join("; "),
        });
        return;
      }
      const { required } = validation.data as { required: boolean };
      identityInputs[identityKey] = required ? "required" : "optional";
      fieldOrder.push(identityKey);
      return;
    }

    if (!(child.type in FIELD_TYPE)) {
      droppedFeatures.push({
        kind: "unknown_component",
        elementId: childId,
        type: child.type,
      });
      return;
    }

    const componentType = child.type as Exclude<
      ComponentType,
      "Form" | "Email" | "Name" | "Phone"
    >;
    const validation = catalog.components[componentType].props.safeParse(
      child.props,
    );
    if (!validation.success) {
      errors.push({
        kind: "invalid_props",
        elementId: childId,
        message: validation.error.issues
          .map((i) => `${i.path.join(".")}: ${i.message}`)
          .join("; "),
      });
      return;
    }

    const props = validation.data as Record<string, any>;
    const name = props.name as string;
    seenNames[name] = [...(seenNames[name] ?? []), childId];

    const baseField: PcFieldBase = {
      label: props.label as string,
      required: props.required as boolean,
    };
    if (typeof props.placeholder === "string" && props.placeholder.length > 0) {
      baseField.placeholder = props.placeholder;
    }
    if (translatedVisibility.length > 0) {
      baseField.visible_when = translatedVisibility;
    }

    let pcField: PcCustomField;
    switch (componentType) {
      case "Text": {
        const text: PcTextField = { ...baseField, field_type: "text" };
        if (props.default_value !== undefined && props.default_value !== null) {
          text.default_value = props.default_value;
        }
        if (props.hidden !== undefined) {
          text.hidden = props.hidden;
        }
        if (
          props.query_param_key !== undefined &&
          props.query_param_key !== null
        ) {
          text.query_param_key = props.query_param_key;
        }
        pcField = text;
        break;
      }
      case "Select": {
        const select: PcSelectField = {
          ...baseField,
          field_type: "select",
          options: props.options as string[],
        };
        if (props.default_value !== undefined && props.default_value !== null) {
          select.default_value = props.default_value;
        }
        pcField = select;
        break;
      }
      case "Radio": {
        const radio: PcRadioField = {
          ...baseField,
          field_type: "radio",
          options: props.options as string[],
        };
        if (props.default_value !== undefined && props.default_value !== null) {
          radio.default_value = props.default_value;
        }
        pcField = radio;
        break;
      }
      case "MultiSelect": {
        const multi: PcMultiSelectField = {
          ...baseField,
          field_type: "multiselect",
          options: props.options as string[],
        };
        if (props.default_value !== undefined && props.default_value !== null) {
          multi.default_value = props.default_value;
        }
        pcField = multi;
        break;
      }
      case "Location": {
        const location: PcLocationField = {
          ...baseField,
          field_type: "location",
        };
        if (props.options !== undefined) {
          location.options = props.options as string[];
        }
        if (props.ip_geolocation_hint !== undefined) {
          location.ip_geolocation_hint = props.ip_geolocation_hint;
        }
        pcField = location;
        break;
      }
      default: {
        const exhaustive: never = componentType;
        throw new Error(`Unhandled component type: ${exhaustive as string}`);
      }
    }
    pcShape[name] = pcField;
    fieldOrder.push(name);
  });

  Object.entries(seenNames).forEach(([name, ids]) => {
    if (ids.length > 1) {
      errors.push({ kind: "duplicate_name", name, elementIds: ids });
    }
  });

  return { pcShape, identityInputs, fieldOrder, droppedFeatures, errors };
}
