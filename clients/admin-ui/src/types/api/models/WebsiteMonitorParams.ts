/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type WebsiteMonitorParams = {
  /**
   * The locations from which the website should be monitored
   */
  locations?: Array<string> | null;
  /**
   * List of domains to exclude from monitoring
   */
  exclude_domains?: Array<string> | null;
};
