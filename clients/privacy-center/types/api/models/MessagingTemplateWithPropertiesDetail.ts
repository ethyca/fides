/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MinimalProperty } from "./MinimalProperty";

export type MessagingTemplateWithPropertiesDetail = {
  id: string;
  type: string;
  is_enabled: boolean;
  properties?: Array<MinimalProperty> | null;
  content: any;
};
