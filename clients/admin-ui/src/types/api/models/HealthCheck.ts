/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DictionaryStatus } from "./DictionaryStatus";
import type { FidesCloudStatus } from "./FidesCloudStatus";
import type { SystemScannerStatus } from "./SystemScannerStatus";
import type { TCFStatus } from "./TCFStatus";

/**
 * Healthcheck schema
 */
export type HealthCheck = {
  core_fides_version: string;
  fidesplus_version: string;
  fidesplus_server: string;
  system_scanner: SystemScannerStatus;
  dictionary: DictionaryStatus;
  fides_cloud: FidesCloudStatus;
  tcf: TCFStatus;
};
