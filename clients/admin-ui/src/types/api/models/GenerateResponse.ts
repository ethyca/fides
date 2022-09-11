/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Dataset } from './Dataset';
import type { System } from './System';

/**
 * The model to house the response for generated infrastructure.
 */
export type GenerateResponse = {
  generate_results?: Array<(Dataset | System)>;
};
