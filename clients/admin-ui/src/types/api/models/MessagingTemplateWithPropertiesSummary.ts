/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { MessagingActionType } from "~/types/api/models/MessagingActionType";
import type { MinimalProperty } from "./MinimalProperty";

export type MessagingTemplateWithPropertiesSummary = {
  id: string;
  type: MessagingActionType;
  is_enabled: boolean;
  properties?: Array<MinimalProperty>;
};
