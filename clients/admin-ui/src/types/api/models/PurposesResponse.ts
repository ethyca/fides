/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MappedPurpose } from "./MappedPurpose";

export type PurposesResponse = {
  purposes: Record<string, MappedPurpose>;
  special_purposes: Record<string, MappedPurpose>;
};
