export type PcFieldType =
  | "text"
  | "select"
  | "multiselect"
  | "radio"
  | "location";

export type VisibilityOperator = "eq" | "ne" | "set" | "empty" | "contains";

export interface VisibilityCondition {
  source_field: string;
  operator: VisibilityOperator;
  value?: string | number;
}

export interface PcFieldBase {
  label: string;
  required?: boolean;
  placeholder?: string;
  visible_when?: VisibilityCondition[];
}

export interface PcTextField extends PcFieldBase {
  field_type: "text";
  default_value?: string | null;
  hidden?: boolean;
  query_param_key?: string | null;
}

export interface PcSelectField extends PcFieldBase {
  field_type: "select";
  options: string[];
  default_value?: string | null;
}

export interface PcRadioField extends PcFieldBase {
  field_type: "radio";
  options: string[];
  default_value?: string | null;
}

export interface PcMultiSelectField extends PcFieldBase {
  field_type: "multiselect";
  options: string[];
  default_value?: string[] | null;
}

export interface PcLocationField extends PcFieldBase {
  field_type: "location";
  options?: string[];
  ip_geolocation_hint?: boolean;
}

export type PcCustomField =
  | PcTextField
  | PcSelectField
  | PcRadioField
  | PcMultiSelectField
  | PcLocationField;

export type PcCustomFields = Record<string, PcCustomField>;

export type DroppedFeature =
  | { kind: "visible"; elementId: string }
  | { kind: "watch"; elementId: string }
  | { kind: "expression"; elementId: string; path: string }
  | { kind: "unknown_component"; elementId: string; type: string };

export type ValidationError =
  | { kind: "duplicate_name"; name: string; elementIds: string[] }
  | { kind: "invalid_props"; elementId: string; message: string }
  | { kind: "missing_form_root"; rootId: string }
  | { kind: "child_not_found"; elementId: string; parentId: string };

export interface MapResult {
  pcShape: PcCustomFields;
  identityInputs: Record<string, "required" | "optional">;
  // Unified render order across identity_inputs and pcShape, in the order the
  // form builder's children list resolved. Persisted as `field_order` on the
  // privacy center action so the public renderer can interleave identity and
  // custom fields freely. Empty if the spec has no children.
  fieldOrder: string[];
  droppedFeatures: DroppedFeature[];
  errors: ValidationError[];
}

export interface JsonRenderElement {
  type: string;
  props: Record<string, unknown>;
  children: string[];
  visible?: unknown;
  watch?: unknown;
}

export interface JsonRenderSpec {
  root: string;
  elements: Record<string, JsonRenderElement>;
}
