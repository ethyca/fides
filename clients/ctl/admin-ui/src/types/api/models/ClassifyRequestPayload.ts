/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DatasetSchema } from './DatasetSchema';
import type { GenerateRequestPayload } from './GenerateRequestPayload';

export type ClassifyRequestPayload = {
  schema_config: GenerateRequestPayload;
  dataset_schemas: Array<DatasetSchema>;
};
