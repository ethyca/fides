import { PrivacyRequestFieldDefinition } from "./types";

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
  privacy_request: "Privacy Request",
  identity: "Identity",
  policy: "Policy",
  location: "Location",
};

export const getCategoryFromFieldPath = (fieldPath: string): string => {
  // "privacy_request.identity.email" -> "Identity"
  // "privacy_request.created_at" -> "Privacy Request"
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
      const category = parts[1]; // "policy", "identity", etc.
      const field = parts.slice(2).join("."); // "name", "has_access_rule", etc.
      const formattedField = field
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
      return `${category.charAt(0).toUpperCase() + category.slice(1)}: ${formattedField}`;
    }
    // Top-level fields like "created_at"
    const field = parts.slice(1).join(".");
    return field
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  }
  return fieldAddress;
};

export const flattenPrivacyRequestFields = (
  data: any,
  allowedFields: string[],
): PrivacyRequestFieldDefinition[] => {
  const flattenedFields: PrivacyRequestFieldDefinition[] = [];

  const flatten = (obj: any, prefix: string = "privacy_request"): void => {
    Object.entries(obj).forEach(([key, val]) => {
      const fieldPath = `${prefix}.${key}`;

      if (val && typeof val === "object" && "field_path" in val) {
        // It's a field definition
        if (allowedFields.includes(fieldPath)) {
          flattenedFields.push(val as PrivacyRequestFieldDefinition);
        }
      } else if (val && typeof val === "object") {
        // It's a nested object, recurse
        flatten(val, fieldPath);
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
