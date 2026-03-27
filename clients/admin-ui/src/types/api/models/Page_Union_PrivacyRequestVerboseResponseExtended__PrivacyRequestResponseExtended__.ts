/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyRequestResponseExtended } from "./PrivacyRequestResponseExtended";
import type { PrivacyRequestVerboseResponseExtended } from "./PrivacyRequestVerboseResponseExtended";

export type Page_Union_PrivacyRequestVerboseResponseExtended__PrivacyRequestResponseExtended__ =
  {
    items: Array<
      PrivacyRequestVerboseResponseExtended | PrivacyRequestResponseExtended
    >;
    total: number;
    page: number;
    size: number;
    pages: number;
  };
