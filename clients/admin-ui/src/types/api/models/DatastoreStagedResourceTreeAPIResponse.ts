/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DiffStatus } from "./DiffStatus";

/**
 * Pydantic Schema used to represent a datastore staged resource children, used only for API responses.
 */
export type DatastoreStagedResourceTreeAPIResponse = {
  urn: string;
  name?: string | null;
  resource_type?: string | null;
  /**
   * The diff status of the staged resource
   */
  diff_status?: DiffStatus | null;
  /**
   * The monitor config that detected this resource
   */
  monitor_config_id: string;
  /**
   * Whether the resource has grandchildren
   */
  has_grandchildren?: boolean;
};
