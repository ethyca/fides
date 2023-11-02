/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { ActionType } from "~/features/privacy-requests/types";
import type { ConnectionType } from "./ConnectionType";
import type { SystemType } from "./SystemType";

/**
 * Describes the returned schema for connection types
 */
export type ConnectionSystemTypeMap = {
  identifier: ConnectionType | string;
  type: SystemType;
  human_readable: string;
  encoded_icon?: string;
  authorization_required?: boolean;
  user_guide?: string;
  supported_actions: Array<ActionType>;
};
