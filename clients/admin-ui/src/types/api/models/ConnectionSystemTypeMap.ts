/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { ConnectionCategory } from "./ConnectionCategory";
import type { ConnectionType } from "./ConnectionType";
import type { IntegrationFeature } from "./IntegrationFeature";
import type { SystemType } from "./SystemType";

/**
 * Describes the returned schema for connection types
 */
export type ConnectionSystemTypeMap = {
  identifier: ConnectionType | string;
  type: SystemType;
  human_readable: string;
  encoded_icon?: string | null;
  authorization_required?: boolean | null;
  user_guide?: string | null;
  supported_actions: Array<ActionType>;
  category?: ConnectionCategory | null;
  tags?: Array<string> | null;
  enabled_features?: Array<IntegrationFeature> | null;
};
