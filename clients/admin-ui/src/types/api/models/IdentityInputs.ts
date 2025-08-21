/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { LocationIdentityField } from "./LocationIdentityField";

export type IdentityInputs = {
  name?: "optional" | "required" | null;
  email?: "optional" | "required" | null;
  phone?: "optional" | "required" | null;
  location?: "optional" | "required" | LocationIdentityField | null;
};
