/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionConfigurationResponse } from "./ConnectionConfigurationResponse";
import type { Dataset_Output } from "./Dataset_Output";

export type SaasConnectionTemplateResponse = {
  connection: ConnectionConfigurationResponse;
  dataset: Dataset_Output;
};
