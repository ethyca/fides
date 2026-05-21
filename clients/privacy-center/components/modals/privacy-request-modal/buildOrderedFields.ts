import { CustomConfigField } from "~/types/config";

type LegacyIdentityKind = "name" | "email" | "phone";
type LegacyMode = "required" | "optional";

export type OrderedField =
  | { kind: LegacyIdentityKind; mode: LegacyMode }
  | { kind: "custom-identity"; key: string; field: CustomConfigField }
  | { kind: "custom"; key: string; field: CustomConfigField };

const LEGACY_IDENTITY_KEYS: readonly LegacyIdentityKind[] = [
  "name",
  "email",
  "phone",
] as const;

const isLegacyIdentityKey = (key: string): key is LegacyIdentityKind =>
  (LEGACY_IDENTITY_KEYS as readonly string[]).includes(key);

const isLegacyMode = (value: unknown): value is LegacyMode =>
  value === "required" || value === "optional";

/**
 * Resolve the list of fields the privacy request form should render, in order.
 *
 * When the action has a `field_order` array, fields render strictly in that
 * sequence — interleaving identity fields with customs is supported, which is
 * how the form builder surfaces "this custom field above email" to end users.
 *
 * When `field_order` is absent (legacy configs) we fall back to the original
 * hardcoded sequence: name → email → phone → custom identities → customs.
 *
 * Configured fields missing from `field_order` are appended at the end via the
 * legacy fallback so a hand-edited YAML adding a field without updating
 * `field_order` doesn't silently disappear.
 */
export const buildOrderedFields = (
  legacyIdentityFields: Record<string, unknown>,
  customIdentityFields: Record<string, CustomConfigField>,
  customPrivacyRequestFields: Record<string, CustomConfigField>,
  fieldOrder?: string[] | null,
): OrderedField[] => {
  const result: OrderedField[] = [];
  const seen = new Set<string>();

  const pushLegacyIdentity = (key: LegacyIdentityKind) => {
    const mode = legacyIdentityFields[key];
    if (!isLegacyMode(mode) || seen.has(key)) {
      return;
    }
    result.push({ kind: key, mode });
    seen.add(key);
  };

  const pushCustomIdentity = (key: string) => {
    const field = customIdentityFields[key];
    if (!field || seen.has(key)) {
      return;
    }
    result.push({ kind: "custom-identity", key, field });
    seen.add(key);
  };

  const pushCustom = (key: string) => {
    const field = customPrivacyRequestFields[key];
    if (!field || seen.has(key)) {
      return;
    }
    result.push({ kind: "custom", key, field });
    seen.add(key);
  };

  if (fieldOrder && fieldOrder.length > 0) {
    fieldOrder.forEach((key) => {
      if (isLegacyIdentityKey(key)) {
        pushLegacyIdentity(key);
      } else if (key in customIdentityFields) {
        pushCustomIdentity(key);
      } else if (key in customPrivacyRequestFields) {
        pushCustom(key);
      }
      // Unknown keys are skipped — backend validation already rejects them
      // at save time; the renderer just stays defensive against stale data.
    });
  }

  // Legacy fallback for any keys not listed in `field_order`.
  LEGACY_IDENTITY_KEYS.forEach(pushLegacyIdentity);
  Object.keys(customIdentityFields).forEach(pushCustomIdentity);
  Object.keys(customPrivacyRequestFields).forEach(pushCustom);

  return result;
};
