/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A summary of a system with aggregate counts for select fields.
 */
export type SystemSummary = {
  id: string;
  fides_key: string;
  vendor_id?: string | null;
  name: string;
  purposes: number;
  cookies: number;
  data_uses: number;
  legal_bases: number;
  consent_categories: number;
};
