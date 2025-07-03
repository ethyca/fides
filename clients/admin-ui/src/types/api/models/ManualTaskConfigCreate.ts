/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ManualTaskConfigurationType } from "./ManualTaskConfigurationType";
import type { ManualTaskFieldBase } from "./ManualTaskFieldBase";

/**
 * Request model for creating manual task configuration.
 */
export type ManualTaskConfigCreate = {
  config_type: ManualTaskConfigurationType;
  fields: Array<ManualTaskFieldBase>;
};
