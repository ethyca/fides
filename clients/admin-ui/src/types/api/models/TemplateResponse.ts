/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for assessment templates.
 */
export type TemplateResponse = {
  id: string;
  key: string;
  version: string;
  name: string;
  assessment_type?: (string | null);
  region?: (string | null);
  authority?: (string | null);
  legal_reference?: (string | null);
  description?: (string | null);
  is_active?: boolean;
};

