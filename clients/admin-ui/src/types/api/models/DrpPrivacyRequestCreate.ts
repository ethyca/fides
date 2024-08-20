/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DrpAction } from "./DrpAction";
import type { DrpMeta } from "./DrpMeta";
import type { DrpRegime } from "./DrpRegime";

/**
 * Data required to create a DRP PrivacyRequest
 */
export type DrpPrivacyRequestCreate = {
  meta: DrpMeta;
  regime?: DrpRegime | null;
  exercise: Array<DrpAction>;
  relationships?: Array<string> | null;
  identity: string;
  status_callback?: string | null;
};
