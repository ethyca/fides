/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AdminUIConfig } from "./AdminUIConfig";
import type { ExecutionApplicationConfig } from "./ExecutionApplicationConfig";
import type { fides__api__schemas__application_config__ConsentConfig } from "./fides__api__schemas__application_config__ConsentConfig";
import type { GPPApplicationConfig } from "./GPPApplicationConfig";
import type { NotificationApplicationConfig } from "./NotificationApplicationConfig";
import type { PlusConsentSettings } from "./PlusConsentSettings";
import type { SecurityApplicationConfig } from "./SecurityApplicationConfig";
import type { StorageApplicationConfig } from "./StorageApplicationConfig";

export type PlusApplicationConfig = {
  storage?: StorageApplicationConfig | null;
  notifications?: NotificationApplicationConfig | null;
  execution?: ExecutionApplicationConfig | null;
  security?: SecurityApplicationConfig | null;
  consent?: fides__api__schemas__application_config__ConsentConfig | null;
  admin_ui?: AdminUIConfig | null;
  gpp?: GPPApplicationConfig | null;
  plus_consent_settings?: PlusConsentSettings | null;
};
