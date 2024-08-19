/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomPrivacyRequestField_Output } from "./CustomPrivacyRequestField_Output";
import type { IdentityInputs } from "./IdentityInputs";

export type PrivacyRequestOption_Output = {
  policy_key: string;
  icon_path: string;
  title: string;
  description: string;
  description_subtext?: Array<string> | null;
  confirmButtonText?: string | null;
  cancelButtonText?: string | null;
  identity_inputs?: IdentityInputs | null;
  custom_privacy_request_fields?: Record<
    string,
    CustomPrivacyRequestField_Output
  > | null;
};
