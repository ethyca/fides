import { isEmpty, isNil } from "lodash";
import { createParser } from "nuqs";

import { IdentityValue, PrivacyRequestResponse } from "~/types/api";

/**
 * Custom nuqs parser for custom_privacy_request_fields
 * Serializes as JSON string in URL query params
 */
export const parseAsCustomFields = createParser({
  parse: (value: string) => {
    try {
      return JSON.parse(value) as Record<string, string | null>;
    } catch {
      return null;
    }
  },
  serialize: (value: Record<string, string | null>) => JSON.stringify(value),
});

interface CustomFieldWithKey {
  key: string;
  label: string;
  value: unknown;
}

interface IdentityValueWithKey extends IdentityValue {
  key: string;
}

const getIdentityValues = (
  key: string,
  identity: string | IdentityValue | null,
): IdentityValueWithKey | null => {
  if (!identity) {
    return null;
  }
  // compatible with old string identity value
  if (typeof identity === "string" && identity.length > 0) {
    return { value: identity, label: key, key };
  }

  // compatible with new object identity value with label and value
  if (typeof identity === "object" && !isEmpty(identity.value)) {
    return { value: identity.value, label: identity.label, key };
  }

  return null;
};

export const getPrimaryIdentity = (
  identity: PrivacyRequestResponse["identity"],
): IdentityValueWithKey | null => {
  if (!identity) {
    return null;
  }

  // email is the primary identity by default
  const emailIdentity = getIdentityValues("email", identity.email);
  if (emailIdentity) {
    return emailIdentity;
  }

  // then we check for phone number
  const phoneNumberIdentity = getIdentityValues(
    "phone_number",
    identity.phone_number,
  );
  if (phoneNumberIdentity) {
    return phoneNumberIdentity;
  }

  // finally, we'll use the first identity
  const keys = Object.keys(identity);
  if (keys.length > 0) {
    return getIdentityValues(keys[0], identity[keys[0]]);
  }

  return null;
};

export const getOtherIdentities = (
  allIdentities: PrivacyRequestResponse["identity"],
  primaryIdentity: IdentityValueWithKey | null,
): IdentityValueWithKey[] => {
  if (!allIdentities) {
    return [];
  }

  return Object.entries(allIdentities)
    .map(([key, identity]) => getIdentityValues(key, identity))
    .filter((identity): identity is IdentityValueWithKey => Boolean(identity))
    .filter((identity) => identity.key !== primaryIdentity?.key);
};

export const getCustomFields = (
  customFields: PrivacyRequestResponse["custom_privacy_request_fields"],
): CustomFieldWithKey[] => {
  if (!customFields) {
    return [];
  }

  return customFields
    ? Object.entries(customFields)
        .filter(([, field]) => !isNil(field.value) && field.value !== "")
        .map(([key, field]) => ({
          key,
          label: field.label,
          value: field.value,
        }))
    : [];
};
