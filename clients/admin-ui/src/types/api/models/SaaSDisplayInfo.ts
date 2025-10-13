/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionCategory } from './ConnectionCategory';
import type { IntegrationFeature } from './IntegrationFeature';

/**
 * Optional display information for SAAS integrations to enhance frontend presentation.
 * When not provided, smart defaults will be inferred based on the integration type.
 */
export type SaaSDisplayInfo = {
  category?: (ConnectionCategory | null);
  tags?: (Array<string> | null);
  enabled_features?: (Array<IntegrationFeature> | null);
};

