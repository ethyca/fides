/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { ColumnSort } from "./ColumnSort";
import type { PrivacyRequestStatus } from "./PrivacyRequestStatus";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type PrivacyRequestFilter = {
  request_id?: string;
  identities?: any;
  custom_privacy_request_fields?: any;
  status?: PrivacyRequestStatus | Array<PrivacyRequestStatus>;
  created_lt?: string;
  created_gt?: string;
  started_lt?: string;
  started_gt?: string;
  completed_lt?: string;
  completed_gt?: string;
  errored_lt?: string;
  errored_gt?: string;
  external_id?: string;
  action_type?: ActionType;
  verbose?: boolean;
  include_identities?: boolean;
  include_custom_privacy_request_fields?: boolean;
  download_csv?: boolean;
  sort_field?: string;
  sort_direction?: ColumnSort;
};
