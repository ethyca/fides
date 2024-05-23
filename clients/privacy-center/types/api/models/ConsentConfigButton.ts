/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__privacy_center_config__CustomPrivacyRequestField } from "./fides__api__schemas__privacy_center_config__CustomPrivacyRequestField";
import type { IdentityInputs } from "./IdentityInputs";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type ConsentConfigButton = {
  description: string;
  description_subtext?: Array<string>;
  confirmButtonText?: string;
  cancelButtonText?: string;
  icon_path: string;
  identity_inputs: IdentityInputs;
  custom_privacy_request_fields?: Record<
    string,
    fides__api__schemas__privacy_center_config__CustomPrivacyRequestField
  >;
  title: string;
  modalTitle?: string;
};
