/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { narrow } from "narrow-minded";
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
};

export const isConnectionSystemTypeMap = (
  obj: unknown
): obj is ConnectionSystemTypeMap =>
  narrow(
    {
      encoded_icon: "string",
    },
    obj
  );
