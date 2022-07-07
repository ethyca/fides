/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AWSConfig } from './AWSConfig';
import type { GenerateTypes } from './GenerateTypes';
import type { OktaConfig } from './OktaConfig';
import type { ValidTargets } from './ValidTargets';

/**
 * Defines attributes for generating resources included in a request.
 */
export type Generate = {
  config: (AWSConfig | OktaConfig);
  target: ValidTargets;
  type: GenerateTypes;
};
