import dayjs, { Dayjs } from "dayjs";

import { formatDate } from "~/features/common/utils";
import { ConditionLeaf, Operator } from "~/types/api";

import {
  CustomFieldMetadata,
  FieldSource,
  PrivacyRequestFieldDefinition,
} from "./types";

// Field type detection
export type FieldType =
  | "boolean"
  | "date"
  | "location"
  | "location_country"
  | "location_groups"
  | "location_regulations"
  | "policy"
  | "string"
  | "custom_select"
  | "custom_multiselect";

// Hardcoded list of date fields
export const DATE_FIELDS = [
  "privacy_request.created_at",
  "privacy_request.requested_at",
  "privacy_request.due_date",
  "privacy_request.identity_verified_at",
];

/**
 * Determines the field type based on the field address.
 * This is used to render appropriate input components for different field types.
 */
export const getFieldType = (fieldAddress: string): FieldType => {
  // Check date fields
  if (DATE_FIELDS.includes(fieldAddress)) {
    return "date";
  }

  // Check location field
  if (fieldAddress === "privacy_request.location") {
    return "location";
  }

  // Check location_country field (convenience field)
  if (fieldAddress === "privacy_request.location_country") {
    return "location_country";
  }

  // Check location_groups field (convenience field)
  if (fieldAddress === "privacy_request.location_groups") {
    return "location_groups";
  }

  // Check location_regulations field (convenience field)
  if (fieldAddress === "privacy_request.location_regulations") {
    return "location_regulations";
  }

  // Check policy ID field
  if (fieldAddress === "privacy_request.policy.key") {
    return "policy";
  }

  // Check boolean fields (known boolean fields in privacy request)
  if (
    fieldAddress.includes("has_access_rule") ||
    fieldAddress.includes("has_erasure_rule") ||
    fieldAddress.includes("has_consent_rule") ||
    fieldAddress.includes("has_update_rule")
  ) {
    return "boolean";
  }

  return "string";
};

/**
 * Determines the field type with custom field metadata support.
 * This extends getFieldType to handle custom fields with select/multiselect types.
 *
 * @param fieldAddress - The field address to check
 * @param customFieldMetadata - Optional custom field metadata for the field
 * @returns The field type
 */
export const getFieldTypeWithMetadata = (
  fieldAddress: string,
  customFieldMetadata: CustomFieldMetadata | null,
): FieldType => {
  // Check if this is a custom field with specific field type
  if (customFieldMetadata) {
    if (customFieldMetadata.field_type === "select") {
      return "custom_select";
    }
    if (customFieldMetadata.field_type === "multiselect") {
      return "custom_multiselect";
    }
    // For text and location custom fields, fall through to standard detection
  }

  // Use standard field type detection
  return getFieldType(fieldAddress);
};

/**
 * Parses a form value into the appropriate type for a condition.
 * Handles Dayjs objects, booleans, numbers, and strings.
 */
export const parseConditionValue = (
  operator: Operator,
  rawValue?: string | boolean | Dayjs,
): string | number | boolean | null => {
  if (operator === Operator.EXISTS || operator === Operator.NOT_EXISTS) {
    return null;
  }

  // Handle Dayjs objects (from DatePicker)
  if (dayjs.isDayjs(rawValue)) {
    return rawValue.toISOString();
  }

  // Handle boolean values directly (from Radio.Group)
  if (typeof rawValue === "boolean") {
    return rawValue;
  }

  // Handle string values
  if (typeof rawValue === "string") {
    if (!rawValue.trim()) {
      return null;
    }

    // Try boolean first
    if (rawValue.toLowerCase() === "true") {
      return true;
    }
    if (rawValue.toLowerCase() === "false") {
      return false;
    }

    // Try number
    const numValue = Number(rawValue);
    if (!Number.isNaN(numValue)) {
      return numValue;
    }

    // Date strings, location strings, location_groups, location_regulations, custom field values pass through as-is
    // Default to string
    return rawValue;
  }

  return null;
};

/**
 * Parses a stored condition value back to the appropriate form value type.
 * This is used when editing an existing condition to populate the form correctly.
 */
export const parseStoredValueForForm = (
  fieldAddress: string,
  storedValue:
    | string
    | number
    | boolean
    | Array<string | number | boolean>
    | null
    | undefined,
): string | boolean | Dayjs | undefined => {
  if (storedValue === null || storedValue === undefined) {
    return undefined;
  }

  const fieldType = getFieldType(fieldAddress);

  // Handle boolean fields
  if (fieldType === "boolean" && typeof storedValue === "boolean") {
    return storedValue;
  }

  // Handle date fields - convert ISO string to Dayjs
  if (fieldType === "date" && typeof storedValue === "string") {
    const parsed = dayjs(storedValue);
    return parsed.isValid() ? parsed : undefined;
  }

  // For all other types (location, location_country, location_groups, location_regulations, policy, string, custom fields), return as string
  return storedValue.toString();
};

// Determine field source based on editing condition
export const getInitialFieldSource = (
  editingCondition?: ConditionLeaf | null,
): FieldSource => {
  if (editingCondition?.field_address) {
    // Privacy request fields start with "privacy_request."
    // Dataset fields contain ":"
    return editingCondition.field_address.startsWith("privacy_request.")
      ? FieldSource.PRIVACY_REQUEST
      : FieldSource.DATASET;
  }
  return FieldSource.PRIVACY_REQUEST;
};

// Allowlist of fields to expose in the UI
// The backend supports many more fields, but that would overwhelm the user with too many options
// so we only expose the most useful fields.
export const ALLOWED_PRIVACY_REQUEST_FIELDS = [
  "privacy_request.created_at",
  "privacy_request.requested_at",
  "privacy_request.due_date",
  "privacy_request.source",
  "privacy_request.identity.email",
  "privacy_request.identity.phone_number",
  "privacy_request.identity.external_id",
  "privacy_request.location",
  "privacy_request.location_country",
  "privacy_request.location_groups",
  "privacy_request.location_regulations",
  "privacy_request.policy.key",
  "privacy_request.policy.has_access_rule",
  "privacy_request.policy.has_erasure_rule",
  "privacy_request.policy.has_consent_rule",
  "privacy_request.policy.has_update_rule",
  "privacy_request.policy.rule_action_types",
  "privacy_request.policy.rule_count",
  "privacy_request.policy.rule_names",
];

export const formatFieldLabel = (fieldPath: string): string => {
  // "privacy_request.identity.email" -> "Email"
  // "privacy_request.policy.has_access_rule" -> "Has access rule"
  const parts = fieldPath.split(".");
  const fieldName = parts[parts.length - 1];
  const words = fieldName.split("_");

  // Sentence case: capitalize only the first word
  return words
    .map((word, index) =>
      index === 0
        ? word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        : word.toLowerCase(),
    )
    .join(" ");
};

// Mapping for category display names
const CATEGORY_LABELS: Record<string, string> = {
  privacy_request: "Privacy request",
  identity: "Identity",
  policy: "Policy",
  location: "Location",
  custom_privacy_request_fields: "Custom fields",
};

export const getCategoryFromFieldPath = (fieldPath: string): string => {
  // "privacy_request.identity.email" -> "Identity"
  // "privacy_request.created_at" -> "Privacy request"
  const parts = fieldPath.split(".");

  if (parts.length === 2) {
    // Top-level field like "privacy_request.created_at"
    const rootCategory = parts[0];
    return CATEGORY_LABELS[rootCategory] || rootCategory;
  }

  // Nested field like "privacy_request.identity.email"
  const category = parts[1];
  return CATEGORY_LABELS[category] || category;
};

export const formatFieldDisplay = (fieldAddress: string): string => {
  // Dataset fields contain ":" (e.g., "dataset:collection:field")
  if (fieldAddress.includes(":")) {
    return fieldAddress.split(":").pop() || fieldAddress;
  }
  // Privacy request fields (e.g., "privacy_request.policy.name")
  if (fieldAddress.startsWith("privacy_request.")) {
    const parts = fieldAddress.split(".");
    if (parts.length >= 3) {
      const category = getCategoryFromFieldPath(fieldAddress);
      const field = parts.slice(2).join("."); // "name", "has_access_rule", etc.
      const formattedField = formatFieldLabel(`privacy_request.${field}`);
      return `${category}: ${formattedField}`;
    }
    // Top-level fields like "created_at"
    const field = parts.slice(1).join(".");
    return formatFieldLabel(`privacy_request.${field}`);
  }
  return fieldAddress;
};

// Type guard to validate PrivacyRequestFieldDefinition at runtime
function isPrivacyRequestFieldDefinition(
  val: unknown,
): val is PrivacyRequestFieldDefinition {
  return (
    typeof val === "object" &&
    val !== null &&
    "field_path" in val &&
    "field_type" in val &&
    "description" in val &&
    "is_convenience_field" in val
  );
}

export const flattenPrivacyRequestFields = (
  data: Record<string, unknown>,
  allowedFields: string[],
): PrivacyRequestFieldDefinition[] => {
  const flattenedFields: PrivacyRequestFieldDefinition[] = [];

  const flatten = (
    obj: Record<string, unknown>,
    prefix: string = "privacy_request",
  ): void => {
    Object.entries(obj).forEach(([key, val]) => {
      const fieldPath = `${prefix}.${key}`;

      if (isPrivacyRequestFieldDefinition(val)) {
        // It's a field definition
        if (allowedFields.includes(fieldPath)) {
          flattenedFields.push(val);
        }
      } else if (val && typeof val === "object") {
        // It's a nested object, recurse
        flatten(val as Record<string, unknown>, fieldPath);
      }
    });
  };

  flatten(data);
  return flattenedFields;
};

export const groupFieldsByCategory = (
  fields: PrivacyRequestFieldDefinition[],
): Array<{
  label: string;
  options: Array<{ label: string; value: string }>;
}> => {
  // Group fields by category
  const grouped = fields.reduce(
    (acc, field) => {
      const category = getCategoryFromFieldPath(field.field_path);
      const existingCategory = acc[category] || [];
      return {
        ...acc,
        [category]: [
          ...existingCategory,
          {
            label: formatFieldLabel(field.field_path),
            value: field.field_path,
          },
        ],
      };
    },
    {} as Record<string, Array<{ label: string; value: string }>>,
  );

  // Convert to Ant Design grouped options format
  return Object.entries(grouped).map(([category, options]) => ({
    label: category,
    options: options.sort((a, b) => a.label.localeCompare(b.label)),
  }));
};

// Operator options for the condition form
export const OPERATOR_OPTIONS = [
  { label: "Equals", value: Operator.EQ },
  { label: "Not equals", value: Operator.NEQ },
  { label: "Greater than", value: Operator.GT },
  { label: "Greater than or equal", value: Operator.GTE },
  { label: "Less than", value: Operator.LT },
  { label: "Less than or equal", value: Operator.LTE },
  { label: "Exists", value: Operator.EXISTS },
  { label: "Does not exist", value: Operator.NOT_EXISTS },
  { label: "List contains", value: Operator.LIST_CONTAINS },
  { label: "Not in list", value: Operator.NOT_IN_LIST },
  { label: "Starts with", value: Operator.STARTS_WITH },
  { label: "Contains", value: Operator.CONTAINS },
];

/**
 * Formats a condition value for display in the UI.
 * Handles dates and other value types appropriately.
 */
export const formatConditionValue = (
  condition: ConditionLeaf,
): string | undefined => {
  const { value, field_address: fieldAddress } = condition;

  if (value === null || value === undefined) {
    return undefined;
  }

  const fieldType = getFieldType(fieldAddress);

  // Format date values
  if (fieldType === "date" && typeof value === "string") {
    try {
      return formatDate(value);
    } catch {
      return String(value);
    }
  }

  // For all other types, convert to string
  return String(value);
};

/**
 * Gets the appropriate tooltip text for the value field based on the field type.
 */
export const getValueTooltip = (
  fieldType: FieldType,
  isValueDisabled: boolean,
): string => {
  if (isValueDisabled) {
    return "Value is not required for exists/not exists operators";
  }

  switch (fieldType) {
    case "boolean":
      return "Select true or false";
    case "date":
      return "Select a date and time";
    case "location":
      return "Select a location";
    case "location_country":
      return "Select a country";
    case "location_groups":
      return "Select a location group (e.g., us, eea, ca)";
    case "location_regulations":
      return "Select a regulation (e.g., gdpr, ccpa, lgpd)";
    case "policy":
      return "Select a policy";
    case "custom_select":
    case "custom_multiselect":
      return "Select a value from the available options";
    default:
      return "Enter the value to compare against. Can be text, number, or true/false";
  }
};
