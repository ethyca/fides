/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__privacy_center_config__CustomPrivacyRequestField } from './fides__api__schemas__privacy_center_config__CustomPrivacyRequestField';
import type { IdentityInputs } from './IdentityInputs';
import type { LocationCustomPrivacyRequestField } from './LocationCustomPrivacyRequestField';

export type ConsentConfigButton = {
  description: string;
  description_subtext?: (Array<string> | null);
  confirmButtonText?: (string | null);
  cancelButtonText?: (string | null);
  icon_path: string;
  identity_inputs: IdentityInputs;
  custom_privacy_request_fields?: (Record<string, (LocationCustomPrivacyRequestField | fides__api__schemas__privacy_center_config__CustomPrivacyRequestField)> | null);
  title: string;
  modalTitle?: (string | null);
};

