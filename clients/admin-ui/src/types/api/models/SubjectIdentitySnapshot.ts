/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { IdentityField } from "./IdentityField";

/**
 * Subset of subject identity values we expose in the list response.
 */
export type SubjectIdentitySnapshot = {
  email?: IdentityField | null;
  phone_number?: IdentityField | null;
};
