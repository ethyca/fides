/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Pydantic Schema used to represent a datastore staged resource children, used only for API responses.
 */
export type DatastoreStagedResourceTreeAPIResponse = {
  urn: string;
  name?: string | null;
  resource_type?: string | null;
  data_type?: string | null;
  /**
   * Whether the resource has children
   */
  has_children: boolean;
  /**
   * The monitor config that detected this resource
   */
  monitor_config_id: string;
};
