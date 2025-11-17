/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClassifyOutput } from "./ClassifyOutput";

/**
 * The result type of the classification, containing a list of classification outputs.
 */
export type ClassifyResult = {
  items: Array<ClassifyOutput>;
  params?: null;
};
