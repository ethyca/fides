/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClassifyInput } from './ClassifyInput';
import type { ClassifyLlmParams } from './ClassifyLlmParams';

export type LLMClassifyRequest = {
  data: Array<ClassifyInput>;
  params?: ClassifyLlmParams;
};

