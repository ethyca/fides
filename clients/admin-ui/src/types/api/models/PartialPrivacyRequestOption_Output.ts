/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomPrivacyRequestField_Output } from "./CustomPrivacyRequestField_Output";
import type { IdentityInputs } from "./IdentityInputs";

export type PartialPrivacyRequestOption_Output = {
  policy_key: string;
  title: string;
  identity_inputs?: IdentityInputs | null;
  custom_privacy_request_fields?: Record<
    string,
    CustomPrivacyRequestField_Output
  > | null;
};
