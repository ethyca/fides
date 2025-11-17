/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fidesplus__v3__schemas__identity__IdentityValue } from "./fidesplus__v3__schemas__identity__IdentityValue";

/**
 * Contains unique identifiers for a subject across multiple systems. Each entry must contain a `value` field and may contain arbitrary key-value pairs for additional metadata. At a minimum, at least one identity must be provided.
 */
export type fidesplus__v3__schemas__identity__Identity = Record<
  string,
  fidesplus__v3__schemas__identity__IdentityValue
>;
