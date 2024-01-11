/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentConfig } from "./ConsentConfig";
import type { ExecutionApplicationConfig } from "./ExecutionApplicationConfig";
import type { GPPApplicationConfig } from "./GPPApplicationConfig";
import type { NotificationApplicationConfig } from "./NotificationApplicationConfig";
import type { SecurityApplicationConfig } from "./SecurityApplicationConfig";
import type { StorageApplicationConfig } from "./StorageApplicationConfig";

/**
 * Application config settings update body is an arbitrary dict (JSON object)
 * We describe it in a schema to enforce some restrictions on the keys passed.
 *
 * TODO: Eventually this should be driven by a more formal validation schema for this
 * the application config that is properly hooked up to the global pydantic config module.
 */
export type PlusApplicationConfig = {
  storage?: StorageApplicationConfig;
  notifications?: NotificationApplicationConfig;
  execution?: ExecutionApplicationConfig;
  security?: SecurityApplicationConfig;
  consent?: ConsentConfig;
  gpp?: GPPApplicationConfig;
};
