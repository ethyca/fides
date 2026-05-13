/* istanbul ignore file */
/* tslint:disable */

import type { Classification } from "./Classification";

export type ClassifyDataFlow = {
  fides_key: string;
  classifications: Array<Classification>;
};
