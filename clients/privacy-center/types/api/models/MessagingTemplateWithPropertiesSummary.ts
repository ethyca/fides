/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MinimalProperty } from "./MinimalProperty";

export type MessagingTemplateWithPropertiesSummary = {
  id: string;
  type: string;
  is_enabled: boolean;
  properties?: Array<MinimalProperty> | null;
};
