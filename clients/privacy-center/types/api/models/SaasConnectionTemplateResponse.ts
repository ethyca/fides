/* istanbul ignore file */
/* tslint:disable */

import type { ConnectionConfigurationResponse } from "./ConnectionConfigurationResponse";
import type { Dataset } from "./Dataset";

export type SaasConnectionTemplateResponse = {
  connection: ConnectionConfigurationResponse;
  dataset: Dataset;
};
