/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { StorageTypeApiAccepted } from "./StorageTypeApiAccepted";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type StorageApplicationConfig = {
  active_default_storage_type: StorageTypeApiAccepted;
};
