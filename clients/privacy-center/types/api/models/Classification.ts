/* istanbul ignore file */
/* tslint:disable */

/**
 * The model for the suggested data labels
 */
export type Classification = {
  label: string;
  score: number;
  rationale?: string | null;
};
