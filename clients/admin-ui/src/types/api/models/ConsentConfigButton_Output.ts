/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomPrivacyRequestField_Output } from "./CustomPrivacyRequestField_Output";
import type { IdentityInputs } from "./IdentityInputs";

export type ConsentConfigButton_Output = {
  description: string;
  description_subtext?: Array<string> | null;
  confirmButtonText?: string | null;
  cancelButtonText?: string | null;
  icon_path: string;
  identity_inputs: IdentityInputs;
  custom_privacy_request_fields?: Record<
    string,
    CustomPrivacyRequestField_Output
  > | null;
  title: string;
  modalTitle?: string | null;
};
