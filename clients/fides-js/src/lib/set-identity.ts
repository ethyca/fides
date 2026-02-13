import { FidesGlobal, SetIdentityOptions } from "./consent-types";
import {
  FIDES_IDENTITY_KEY_EXTERNAL_ID,
  FIDES_IDENTITY_KEY_USER_DEVICE_ID,
  FIDES_IDENTITY_OPTION_KEY_EXTERNAL_ID,
  RESERVED_IDENTITY_KEYS,
  saveFidesCookie,
  SUPPORTED_SET_IDENTITY_KEYS,
  VERIFIED_IDENTITY_KEYS,
} from "./cookie";

function validateSetIdentityKeys(identity: SetIdentityOptions): void {
  const keys = Object.keys(identity) as (keyof SetIdentityOptions)[];
  keys.forEach((key) => {
    if (
      RESERVED_IDENTITY_KEYS.includes(
        key as (typeof RESERVED_IDENTITY_KEYS)[number],
      )
    ) {
      throw new Error(
        `${FIDES_IDENTITY_KEY_USER_DEVICE_ID} is reserved and cannot be set via setIdentity.`,
      );
    }
    if (
      VERIFIED_IDENTITY_KEYS.includes(
        key as (typeof VERIFIED_IDENTITY_KEYS)[number],
      )
    ) {
      throw new Error(
        "email and phone_number are verified identity keys and cannot be set via setIdentity.",
      );
    }
    if (
      !SUPPORTED_SET_IDENTITY_KEYS.includes(
        key as (typeof SUPPORTED_SET_IDENTITY_KEYS)[number],
      )
    ) {
      throw new Error(
        `Only ${FIDES_IDENTITY_OPTION_KEY_EXTERNAL_ID} is supported. Unsupported key: ${key}.`,
      );
    }
  });
}

/**
 * Set identity fields on the Fides cookie (e.g. fides_external_id).
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

  const externalId = identity[FIDES_IDENTITY_OPTION_KEY_EXTERNAL_ID];
  if (externalId === undefined) {
    return;
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
