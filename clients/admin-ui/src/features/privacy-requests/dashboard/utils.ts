import { PrivacyRequestEntity } from "../types";

interface IdentityWithKey {
  key: string;
  label: string;
  value: string;
}

interface CustomFieldWithKey {
  key: string;
  label: string;
  value: any;
}

export const getPrimaryIdentity = (
  identity: PrivacyRequestEntity["identity"],
): IdentityWithKey | null => {
  // email is the primary identity by default
  if (identity.email && identity.email.value) {
    return { key: "email", ...identity.email };
  }

  // then we check for phone number
  if (identity.phone_number && identity.phone_number.value) {
    return { key: "phone_number", ...identity.phone_number };
  }

  // finally, we'll use the first identity
  const keys = Object.keys(identity);
  if (keys.length > 0) {
    return { key: keys[0], ...identity[keys[0]] };
  }

  return null;
};

export const getOtherIdentities = (
  allIdentities: PrivacyRequestEntity["identity"],
  primaryIdentity: IdentityWithKey | null,
): IdentityWithKey[] => {
  return Object.entries(allIdentities)
    .filter(([key, identity]) => (identity.value !== null && identity.value !== undefined && identity.value !== "") && key !== primaryIdentity?.key)
    .map(([key, identity]) => ({
      key,
      ...identity,
    }));
};

export const getCustomFields = (
  customFields: PrivacyRequestEntity["custom_privacy_request_fields"],
): CustomFieldWithKey[] => {
  return customFields
    ? Object.entries(customFields)
        .filter(([, field]) => field.value !== null && field.value !== undefined && field.value !== "")
        .map(([key, field]) => ({
          key,
          label: field.label,
          value: field.value,
        }))
    : [];
};
