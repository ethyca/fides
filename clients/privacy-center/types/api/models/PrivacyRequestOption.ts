/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__privacy_center_config__CustomPrivacyRequestField } from './fides__api__schemas__privacy_center_config__CustomPrivacyRequestField';
import type { IdentityInputs } from './IdentityInputs';

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type PrivacyRequestOption = {
  policy_key: string;
  icon_path: string;
  title: string;
  description: string;
  description_subtext?: Array<string>;
  confirmButtonText?: string;
  cancelButtonText?: string;
  identity_inputs?: IdentityInputs;
  custom_privacy_request_fields?: Record<string, fides__api__schemas__privacy_center_config__CustomPrivacyRequestField>;
};

