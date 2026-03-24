/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DictionaryStatus } from "./DictionaryStatus";
import type { FidesCloudStatus } from "./FidesCloudStatus";
import type { TCFStatus } from "./TCFStatus";

/**
 * Healthcheck schema
 */
export type HealthCheck = {
  core_fides_version: string;
  fidesplus_version: string;
  fidesplus_server: string;
  dictionary: DictionaryStatus;
  fides_cloud: FidesCloudStatus;
  tcf: TCFStatus;
};
