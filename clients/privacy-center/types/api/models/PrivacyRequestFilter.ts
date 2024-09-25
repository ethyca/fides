/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { ColumnSort } from "./ColumnSort";
import type { PrivacyRequestStatus } from "./PrivacyRequestStatus";

export type PrivacyRequestFilter = {
  request_id?: string | null;
  identities?: null;
  fuzzy_search_str?: string | null;
  custom_privacy_request_fields?: null;
  status?: PrivacyRequestStatus | Array<PrivacyRequestStatus> | null;
  created_lt?: string | null;
  created_gt?: string | null;
  started_lt?: string | null;
  started_gt?: string | null;
  completed_lt?: string | null;
  completed_gt?: string | null;
  errored_lt?: string | null;
  errored_gt?: string | null;
  external_id?: string | null;
  action_type?: ActionType | null;
  verbose?: boolean | null;
  include_identities?: boolean | null;
  include_custom_privacy_request_fields?: boolean | null;
  download_csv?: boolean | null;
  sort_field?: string;
  sort_direction?: ColumnSort;
};
