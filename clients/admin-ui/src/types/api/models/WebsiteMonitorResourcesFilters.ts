/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentStatus } from './ConsentStatus';

export type WebsiteMonitorResourcesFilters = {
  resource_type?: (Array<string> | null);
  locations?: (Array<string> | null);
  consent_aggregated?: (Array<ConsentStatus> | null);
  data_uses?: (Array<string> | null);
};

