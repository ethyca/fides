/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * API schema for Assets, very basic for now
 */
export type Asset = {
  id: string;
  name: string;
  asset_type: string;
  system_id: string;
  domain?: string | null;
  parent?: Array<string>;
  parent_domain?: string | null;
  locations?: Array<string>;
  with_consent?: boolean;
  data_uses?: Array<string>;
  path?: string | null;
  base_url?: string | null;
};
