/* istanbul ignore file */
/* tslint:disable */

import type { PrivacyRequestResponse } from "./PrivacyRequestResponse";
import type { PrivacyRequestVerboseResponse } from "./PrivacyRequestVerboseResponse";

export type Page_Union_PrivacyRequestVerboseResponse__PrivacyRequestResponse__ =
  {
    items: Array<PrivacyRequestVerboseResponse | PrivacyRequestResponse>;
    total: number | null;
    page: number | null;
    size: number | null;
    pages?: number | null;
  };
