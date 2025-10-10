/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ErrorNotificationMode } from "./ErrorNotificationMode";

export type AdminUIConfig = {
  enabled?: boolean | null;
  url?: string | null;
  error_notification_mode?: ErrorNotificationMode | null;
};
