import dayjs, { Dayjs } from "dayjs";

import { formatDate } from "~/features/common/utils";
import { ConditionLeaf, Operator } from "~/types/api";

import { FieldValue } from "./components/ConditionValueSelector";
import {
  CustomFieldMetadata,
  FieldSource,
  PrivacyRequestFieldDefinition,
} from "./types";

/**
 * Backend-defined field addresses for the privacy request condition system.
 * These are dot-path addresses into the PrivacyRequest model, used for
 * conditional dependency evaluation.
 */
export const PrivacyRequestField = {
  CREATED_AT: "privacy_request.created_at",
  REQUESTED_AT: "privacy_request.requested_at",
  DUE_DATE: "privacy_request.due_date",
  IDENTITY_VERIFIED_AT: "privacy_request.identity_verified_at",
  SOURCE: "privacy_request.source",
  IDENTITY_EMAIL: "privacy_request.identity.email",
  IDENTITY_PHONE_NUMBER: "privacy_request.identity.phone_number",
  IDENTITY_EXTERNAL_ID: "privacy_request.identity.external_id",
  LOCATION: "privacy_request.location",
  LOCATION_COUNTRY: "privacy_request.location_country",
  LOCATION_GROUPS: "privacy_request.location_groups",
  LOCATION_REGULATIONS: "privacy_request.location_regulations",
  POLICY_KEY: "privacy_request.policy.key",
  POLICY_HAS_ACCESS_RULE: "privacy_request.policy.has_access_rule",
  POLICY_HAS_ERASURE_RULE: "privacy_request.policy.has_erasure_rule",
  POLICY_HAS_CONSENT_RULE: "privacy_request.policy.has_consent_rule",
  POLICY_HAS_UPDATE_RULE: "privacy_request.policy.has_update_rule",
  POLICY_RULE_ACTION_TYPES: "privacy_request.policy.rule_action_types",
  POLICY_RULE_COUNT: "privacy_request.policy.rule_count",
  POLICY_RULE_NAMES: "privacy_request.policy.rule_names",
  CUSTOM_FIELDS_PREFIX: "privacy_request.custom_privacy_request_fields.",
} as const;

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

export const DATE_FIELDS: string[] = [
  PrivacyRequestField.CREATED_AT,
  PrivacyRequestField.REQUESTED_AT,
  PrivacyRequestField.DUE_DATE,
  PrivacyRequestField.IDENTITY_VERIFIED_AT,
];

const FIELD_TYPE_MAP: Partial<Record<string, FieldType>> = {
  [PrivacyRequestField.LOCATION]: "location",
  [PrivacyRequestField.LOCATION_COUNTRY]: "location_country",
  [PrivacyRequestField.LOCATION_GROUPS]: "location_groups",
  [PrivacyRequestField.LOCATION_REGULATIONS]: "location_regulations",
  [PrivacyRequestField.POLICY_KEY]: "policy",
  [PrivacyRequestField.POLICY_HAS_ACCESS_RULE]: "boolean",
  [PrivacyRequestField.POLICY_HAS_ERASURE_RULE]: "boolean",
  [PrivacyRequestField.POLICY_HAS_CONSENT_RULE]: "boolean",
  [PrivacyRequestField.POLICY_HAS_UPDATE_RULE]: "boolean",
};

/**
 * Determines the field type based on the field address.
 * This is used to render appropriate input components for different field types.
 */
export const getFieldType = (fieldAddress: string): FieldType => {
  if (DATE_FIELDS.includes(fieldAddress)) {
    return "date";
  }
  return FIELD_TYPE_MAP[fieldAddress] ?? "string";
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
  rawValue?: FieldValue,
): FieldValue => {
  if (operator === Operator.EXISTS || operator === Operator.NOT_EXISTS) {
    return null;
  }

  // Handle array values (from multiselect)
  if (Array.isArray(rawValue)) {
    return rawValue;
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
): string | boolean | Dayjs | string[] | undefined => {
  if (storedValue === null || storedValue === undefined) {
    return undefined;
  }

  // Handle array values (from multiselect location fields)
  if (Array.isArray(storedValue)) {
    return storedValue.map(String);
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

// Allowlist of fields to expose in the UI.
// The backend supports many more fields, but that would overwhelm the user
// with too many options so we only expose the most useful fields.
export const ALLOWED_PRIVACY_REQUEST_FIELDS = [
  PrivacyRequestField.CREATED_AT,
  PrivacyRequestField.REQUESTED_AT,
  PrivacyRequestField.DUE_DATE,
  PrivacyRequestField.SOURCE,
  PrivacyRequestField.IDENTITY_EMAIL,
  PrivacyRequestField.IDENTITY_PHONE_NUMBER,
  PrivacyRequestField.IDENTITY_EXTERNAL_ID,
  PrivacyRequestField.LOCATION,
  PrivacyRequestField.LOCATION_COUNTRY,
  PrivacyRequestField.LOCATION_GROUPS,
  PrivacyRequestField.LOCATION_REGULATIONS,
  PrivacyRequestField.POLICY_KEY,
  PrivacyRequestField.POLICY_HAS_ACCESS_RULE,
  PrivacyRequestField.POLICY_HAS_ERASURE_RULE,
  PrivacyRequestField.POLICY_HAS_CONSENT_RULE,
  PrivacyRequestField.POLICY_HAS_UPDATE_RULE,
  PrivacyRequestField.POLICY_RULE_ACTION_TYPES,
  PrivacyRequestField.POLICY_RULE_COUNT,
  PrivacyRequestField.POLICY_RULE_NAMES,
];

// Fields that are NOT available for consent requests.
// Consent DSRs don't have execution timeframes (no due_date) and don't have
// data flowing between nodes (dataset fields handled separately).
export const CONSENT_UNAVAILABLE_FIELDS: string[] = [
  PrivacyRequestField.DUE_DATE,
];

// Allowlist of fields available for consent-only manual task conditions
// This is a subset of ALLOWED_PRIVACY_REQUEST_FIELDS excluding fields not captured for consent
export const CONSENT_ALLOWED_PRIVACY_REQUEST_FIELDS =
  ALLOWED_PRIVACY_REQUEST_FIELDS.filter(
    (field) => !CONSENT_UNAVAILABLE_FIELDS.includes(field),
  );

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
