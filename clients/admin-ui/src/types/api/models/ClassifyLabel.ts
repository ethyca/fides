/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Label and score for a classification output.
 */
export type ClassifyLabel = {
  value: string;
  score: number;
  rationale?: (string | null);
};

