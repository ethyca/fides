/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__privacy_center_config__CustomPrivacyRequestField } from "./fides__api__schemas__privacy_center_config__CustomPrivacyRequestField";
import type { IdentityInputs } from "./IdentityInputs";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

export type PrivacyRequestOption = {
  locations?: Array<PrivacyNoticeRegion> | "fallback" | null;
  policy_key?: string | null;
  icon_path: string;
  title: string;
  description: string;
  description_subtext?: Array<string> | null;
  confirmButtonText?: string | null;
  cancelButtonText?: string | null;
  identity_inputs?: IdentityInputs | null;
  custom_privacy_request_fields?: Record<
    string,
    fides__api__schemas__privacy_center_config__CustomPrivacyRequestField
  > | null;
};
