/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for the suggested data labels
 */
export type Classification = {
  label: string;
  score: number;
  aggregated_score?: number | null;
  classification_paradigm?: string | null;
};
