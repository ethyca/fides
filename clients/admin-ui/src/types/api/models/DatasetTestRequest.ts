/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UnlabeledIdentities } from "./UnlabeledIdentities";

/**
 * The policy key and inputs required to run a dataset test.
 */
export type DatasetTestRequest = {
  policy_key: string;
  identities: UnlabeledIdentities;
};
