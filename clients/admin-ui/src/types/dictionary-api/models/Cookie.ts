/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CookieType } from "./CookieType";

/**
 * A Compass cookie record, extending a fideslang `Cookie`
 */
export type Cookie = {
  name: string;
  path?: string;
  domain?: string;
  type: CookieType;
  /**
   * Whether the cookie is refreshed after being initially set.
   */
  cookie_refresh?: boolean;
  /**
   * The maximum storage duration, in seconds, for this cookie.
   */
  max_age_seconds?: number;
  /**
   * Whether the associated Vendor record uses non-cookie methods of storage or accessing information stored on a user's device.
   */
  uses_non_cookie_access?: boolean;
  /**
   * The record's GVL purposes
   */
  purposes?: Array<number>;
  /**
   * The record's GVL special purposes
   */
  special_purposes?: Array<number>;
  /**
   * The record's GVL features
   */
  features?: Array<number>;
  /**
   * The record's GVL special features
   */
  special_features?: Array<number>;
  /**
   * The ID of the vendor that the record belongs to
   */
  vendor_id: string;
  /**
   * The name of the vendor that the record belongs to
   */
  vendor_name: string;
  /**
   * The version of GVL from which the record is derived
   */
  gvl_version?: string;
  /**
   * A unique identifier for a Cookie record to be used in the Compass data store. Combines other fields that form uniqueness criteria for a Cookie record.
   */
  unique_id?: string;
};
