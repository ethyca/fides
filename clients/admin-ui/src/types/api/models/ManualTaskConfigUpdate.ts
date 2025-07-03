/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ManualTaskConfigurationType } from "./ManualTaskConfigurationType";
import type { ManualTaskFieldBase } from "./ManualTaskFieldBase";

/**
 * Request model for updating manual task configuration.
 */
export type ManualTaskConfigUpdate = {
  config_type: ManualTaskConfigurationType;
  fields: Array<ManualTaskFieldBase>;
};
