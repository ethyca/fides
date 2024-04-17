/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";

/**
 * Base API model that represents a staged resource, fields common to all types of staged resources
 */
export type Schema = {
  urn: string;
  user_assigned_data_categories?: Array<string>;
  name: string;
  description?: string;
  modified?: string;
  classifications?: Array<Classification>;
  tables?: Array<string>;
};
