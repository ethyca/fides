/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClassifyInput } from "./ClassifyInput";
import type { ClassifyLabel } from "./ClassifyLabel";

/**
 * Output of a classification, containing the possibly multiple result labels and the input(s) used.
 */
export type ClassifyOutput = {
  labels: Array<ClassifyLabel>;
  input: ClassifyInput | Array<ClassifyInput>;
};
