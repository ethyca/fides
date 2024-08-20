/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__privacy_center_config__CustomPrivacyRequestField } from "./fides__api__schemas__privacy_center_config__CustomPrivacyRequestField";
import type { IdentityInputs } from "./IdentityInputs";

export type PartialPrivacyRequestOption = {
  policy_key: string;
  title: string;
  identity_inputs?: IdentityInputs | null;
  custom_privacy_request_fields?: Record<
    string,
    fides__api__schemas__privacy_center_config__CustomPrivacyRequestField
  > | null;
};
