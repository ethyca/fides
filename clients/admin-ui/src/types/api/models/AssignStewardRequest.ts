/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request schema for assigning a data steward to one or more systems.
 */
export type AssignStewardRequest = {
  data_steward: string;
  system_keys: Array<string>;
};

