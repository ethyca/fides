/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionConfigurationResponse } from "./ConnectionConfigurationResponse";
import type { Dataset } from "./Dataset";

export type SaasConnectionTemplateResponse = {
  connection: ConnectionConfigurationResponse;
  dataset: Dataset;
};
