/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { StorageType } from "./StorageType";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type StorageApplicationConfig = {
  active_default_storage_type: StorageType;
};
