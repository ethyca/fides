import { FidesGlobal, SetIdentityOptions } from "./consent-types";
import {
  FIDES_IDENTITY_KEY_EXTERNAL_ID,
  FIDES_IDENTITY_KEY_USER_DEVICE_ID,
  FIDES_RESERVED_IDENTITY_KEYS,
  FIDES_SUPPORTED_SET_IDENTITY_KEYS,
  FIDES_VERIFIED_IDENTITY_KEYS,
  normalizeIdentityValue,
  saveFidesCookie,
} from "./cookie";

function validateSetIdentityKeys(identity: SetIdentityOptions): void {
  const keys = Object.keys(identity) as (keyof SetIdentityOptions)[];
  keys.forEach((key) => {
    if (
      FIDES_RESERVED_IDENTITY_KEYS.includes(
        key as (typeof FIDES_RESERVED_IDENTITY_KEYS)[number],
      )
    ) {
      throw new Error(
        `${FIDES_IDENTITY_KEY_USER_DEVICE_ID} is reserved and cannot be set via setIdentity.`,
      );
    }
    if (
      FIDES_VERIFIED_IDENTITY_KEYS.includes(
        key as (typeof FIDES_VERIFIED_IDENTITY_KEYS)[number],
      )
    ) {
      throw new Error(
        "email and phone_number are verified identity keys and cannot be set via setIdentity.",
      );
    }
    if (
      !FIDES_SUPPORTED_SET_IDENTITY_KEYS.includes(
        key as (typeof FIDES_SUPPORTED_SET_IDENTITY_KEYS)[number],
      )
    ) {
      throw new Error(
        `Only ${FIDES_IDENTITY_KEY_EXTERNAL_ID} is supported. Unsupported key: ${key}.`,
      );
    }
  });
}

/**
 * Set identity fields on the Fides cookie (e.g. external_id).
 * Validates keys and persists the cookie. Call after Fides.init().
 */
export async function setIdentity(
  this: FidesGlobal,
  identity: SetIdentityOptions,
): Promise<void> {
  if (!this.cookie) {
    throw new Error("Fides must be initialized before calling setIdentity.");
  }
  validateSetIdentityKeys(identity);

  const rawExternalId = identity[FIDES_IDENTITY_KEY_EXTERNAL_ID];
  if (rawExternalId === undefined) {
    return;
  }
  const externalId = normalizeIdentityValue(rawExternalId);
  if (externalId === undefined) {
    throw new Error(
      "external_id cannot be empty or whitespace-only. Omit the key to leave identity unchanged.",
    );
  }

  const hadOverride =
    this.options?.fidesExternalId != null &&
    this.options.fidesExternalId !== "";
  if (hadOverride) {
    fidesDebugger(
      "setIdentity: overriding existing fidesExternalId from init options with value from setIdentity.",
    );
  }

  this.cookie.identity[FIDES_IDENTITY_KEY_EXTERNAL_ID] = externalId;
  await saveFidesCookie(this.cookie, this.options ?? {});
}
