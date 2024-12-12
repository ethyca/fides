/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Extension of SystemResponse response model to include other relationships only needed for Data Catalog view
 */
export type CatalogSystemResponse = {
  id: string;
  fides_key: string;
  name: string | null;
  legal_name: string | null;
  description: string | null;
  system_type: string | null;
  hidden: boolean;
  monitor_config_keys?: Array<string>;
};
