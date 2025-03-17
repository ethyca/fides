/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema for creating a new asset with immutable fields
 */
export type AssetCreate = {
  data_uses?: Array<string>;
  description?: string | null;
  name: string;
  asset_type: string;
  domain: string;
  base_url?: string | null;
  locations?: Array<string>;
};
