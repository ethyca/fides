/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DiffStatus } from "./DiffStatus";
import type { TreeResourceChangeIndicator } from "./TreeResourceChangeIndicator";

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
   * A map of diff statuses present in the descendants of this resource, e.g. {'addition': true}
   */
  child_diff_statuses?: Record<string, boolean> | null;
  /**
   * Indicates if the resource has been added, removed, or changed
   */
  update_status?: TreeResourceChangeIndicator | null;
  /**
   * Whether the resource has grandchildren
   */
  has_grandchildren?: boolean | null;
};
