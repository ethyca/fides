/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyExperienceResponse } from "./PrivacyExperienceResponse";
import type { TCFBannerExperienceMinimalResponse } from "./TCFBannerExperienceMinimalResponse";

export type Page_Union_PrivacyExperienceResponse__TCFBannerExperienceMinimalResponse__ =
  {
    items: Array<
      PrivacyExperienceResponse | TCFBannerExperienceMinimalResponse
    >;
    total: number | null;
    page: number | null;
    size: number | null;
    pages?: number | null;
  };
