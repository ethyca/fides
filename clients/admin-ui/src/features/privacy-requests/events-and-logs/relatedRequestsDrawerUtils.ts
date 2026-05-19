import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

// Pulls the identity fields with non-empty values off the current request.
// Returns both the API filter payload (field_name -> value) and the
// human-readable labels to show in the drawer description. The backend
// OR-matches across fields (see filter_privacy_request_queryset), which is
// what we want for "related requests": a later request that adds a phone
// number still surfaces alongside an earlier email-only one from the same
// person.
export const extractIdentityFields = (
  identity: PrivacyRequestEntity["identity"] | undefined,
): { filter: Record<string, string>; labels: string[] } | undefined => {
  if (!identity) {
    return undefined;
  }
  const filter: Record<string, string> = {};
  const labels: string[] = [];
  Object.entries(identity).forEach(([fieldName, field]) => {
    const value = field?.value;
    if (typeof value !== "string" || value.length === 0) {
      return;
    }
    filter[fieldName] = value;
    labels.push(field.label);
  });
  if (labels.length === 0) {
    return undefined;
  }
  return { filter, labels };
};

export const formatLabelList = (labels: string[]): string => {
  if (labels.length === 0) {
    return "";
  }
  if (labels.length === 1) {
    return labels[0];
  }
  if (labels.length === 2) {
    return `${labels[0]} or ${labels[1]}`;
  }
  return `${labels.slice(0, -1).join(", ")}, or ${labels[labels.length - 1]}`;
};
