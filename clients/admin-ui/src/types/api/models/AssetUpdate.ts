/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema for updating an asset's mutable fields.
 * Changing any other fields would effectively create a new asset
 */
export type AssetUpdate = {
  data_uses?: Array<string> | null;
  description?: string | null;
  /**
   * Human-readable duration for which this asset persists (e.g., cookie lifetime)
   */
  duration?: string | null;
  id: string;
  system_key?: string | null;
  system_id?: string | null;
};
