/* istanbul ignore file */
/* tslint:disable */

import type { MappedPurpose } from "./MappedPurpose";

export type PurposesResponse = {
  purposes: Record<string, MappedPurpose>;
  special_purposes: Record<string, MappedPurpose>;
};
