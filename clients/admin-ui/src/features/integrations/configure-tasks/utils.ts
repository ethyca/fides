import { ConditionLeaf } from "~/types/api";

import { FieldSource, PrivacyRequestFieldDefinition } from "./types";

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
  return FieldSource.DATASET;
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
  "privacy_request.policy.id",
  "privacy_request.policy.name",
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
